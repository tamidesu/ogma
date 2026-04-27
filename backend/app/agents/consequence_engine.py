"""
ConsequenceEngine — applies bounded world-state deltas + may spawn complications.

Single Groq call (temp 0.3). The LLM output is sandboxed against the brief's
declared schema — unknown keys are silently dropped with a structlog warning.
This keeps the simulation grounded even if the LLM drifts outside scope.
"""
from __future__ import annotations

import json
from pathlib import Path

import structlog

from app.agents.groq_helper import call_groq_json
from app.agents.schemas import (
    Intent, NPCUpdate, ScenarioBriefData, SkillXPGain,
    ValidationResult, WorldDelta,
)

logger = structlog.get_logger(__name__)

_PROMPT_PATH = Path(__file__).parent / "prompts" / "consequence_engine.system.md"

_SAFE_DELTA = WorldDelta(
    metric_delta={},
    state_set={},
    time_advance_min=0,
    new_complication=None,
    skill_xp=[],
)


def _build_user_prompt(
    intent: Intent,
    validation: ValidationResult,
    npc_update: NPCUpdate,
    brief: ScenarioBriefData,
    world_state: dict,
    turn_index: int,
) -> str:
    initial = brief.initial_world_state
    metric_keys = list((initial.get("metrics") or {}).keys())
    flag_keys = [f"flags.{k}" for k in (initial.get("flags") or {}).keys()]
    time_keys = [f"time.{k}" for k in (initial.get("time") or {}).keys()]
    diag_keys = [f"diagnosis.{k}" for k in (initial.get("diagnosis") or {}).keys()]
    all_state_keys = flag_keys + time_keys + diag_keys

    return "\n".join([
        "## Brief schema (ONLY allowed keys)",
        f"metric keys: {json.dumps(metric_keys, ensure_ascii=False)}",
        f"state_set keys: {json.dumps(all_state_keys, ensure_ascii=False)}",
        "",
        "## complication_pool",
        json.dumps(brief.complication_pool, ensure_ascii=False),
        "",
        "## current world_state",
        json.dumps(world_state, ensure_ascii=False),
        "",
        "## turn_index",
        str(turn_index),
        "",
        "## intent",
        json.dumps(intent.to_dict(), ensure_ascii=False),
        "",
        "## validation",
        json.dumps(validation.to_dict(), ensure_ascii=False),
        "",
        "## npc_update",
        json.dumps({"new_state_label": npc_update.new_state_label,
                    "relationship_delta": npc_update.relationship_delta}, ensure_ascii=False),
        "",
        f"## locale\n{brief.locale}",
    ])


def _enforce_bounds(
    metric_delta: dict,
    state_set: dict,
    brief: ScenarioBriefData,
) -> tuple:
    """Drop any keys outside the brief's declared schema."""
    initial = brief.initial_world_state
    allowed_metrics = set((initial.get("metrics") or {}).keys())
    allowed_flags = {f"flags.{k}" for k in (initial.get("flags") or {}).keys()}
    allowed_time = {f"time.{k}" for k in (initial.get("time") or {}).keys()}
    allowed_diag = {f"diagnosis.{k}" for k in (initial.get("diagnosis") or {}).keys()}
    allowed_state = allowed_flags | allowed_time | allowed_diag

    clean_metrics: dict = {}
    for k, v in metric_delta.items():
        if k in allowed_metrics:
            clean_metrics[k] = max(-30.0, min(30.0, float(v)))
        else:
            logger.warning("consequence_engine_illegal_metric_key", key=k)

    clean_state: dict = {}
    for k, v in state_set.items():
        if k in allowed_state:
            clean_state[k] = v
        else:
            logger.warning("consequence_engine_illegal_state_key", key=k)

    return clean_metrics, clean_state


def _parse_world_delta(data: dict, brief: ScenarioBriefData) -> WorldDelta:
    metric_raw = data.get("metric_delta") or {}
    state_raw = data.get("state_set") or {}

    metric_delta, state_set = _enforce_bounds(metric_raw, state_raw, brief)

    time_advance = max(0, int(float(data.get("time_advance_min", 0))))

    raw_complication = data.get("new_complication")
    new_complication = None
    if isinstance(raw_complication, dict) and raw_complication.get("id"):
        pool_ids = {c.get("id") for c in brief.complication_pool if isinstance(c, dict)}
        if raw_complication["id"] in pool_ids:
            new_complication = raw_complication
        else:
            logger.warning("consequence_engine_unknown_complication",
                           id=raw_complication.get("id"))

    raw_xp = data.get("skill_xp") or []
    skill_xp = []
    for item in raw_xp:
        if not isinstance(item, dict):
            continue
        skill = str(item.get("skill", "")).strip()
        xp = max(0, min(50, int(float(item.get("xp", 0)))))
        if skill and xp > 0:
            skill_xp.append(SkillXPGain(skill=skill, xp=xp))

    return WorldDelta(
        metric_delta=metric_delta,
        state_set=state_set,
        time_advance_min=time_advance,
        new_complication=new_complication,
        skill_xp=skill_xp,
    )


class ConsequenceEngine:

    async def resolve(
        self,
        intent: Intent,
        validation: ValidationResult,
        npc_update: NPCUpdate,
        brief: ScenarioBriefData,
        world_state: dict,
        turn_index: int,
    ) -> WorldDelta:
        system = _PROMPT_PATH.read_text(encoding="utf-8")
        user = _build_user_prompt(intent, validation, npc_update, brief, world_state, turn_index)

        try:
            data = await call_groq_json(
                system_prompt=system,
                user_prompt=user,
                max_tokens=380,
                temperature=0.3,
                schema_hint="WorldDelta",
            )
            delta = _parse_world_delta(data, brief)
            logger.info(
                "consequence_resolved",
                metrics_changed=list(delta.metric_delta.keys()),
                time_advance=delta.time_advance_min,
                complication=bool(delta.new_complication),
                xp_skills=[g.skill for g in delta.skill_xp],
            )
            return delta
        except Exception as e:
            logger.warning("consequence_engine_fallback", error=str(e))
            return _SAFE_DELTA
