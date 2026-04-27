"""
NPCDirector — updates the unified NPC's emotion + generates in-character dialogue.

Single Groq call, temperature 0.7, max_tokens 280.
The NPC definition + current emotion + rolling memory are injected into the
user prompt so the model has full character context each turn.
Falls back to a neutral "I need a moment" response on error.
"""
from __future__ import annotations

import json
from pathlib import Path

import structlog

from app.agents.groq_helper import call_groq_json
from app.agents.schemas import Intent, NPCMemoryItem, NPCUpdate, ScenarioBriefData, ValidationResult

logger = structlog.get_logger(__name__)

_PROMPT_PATH = Path(__file__).parent / "prompts" / "npc_director.system.md"

_NEUTRAL_FALLBACK = NPCUpdate(
    emotion_delta={"trust": 0, "fear": 0, "anger": 0, "hope": 0},
    relationship_delta=0,
    new_state_label="calm_engaged",
    utterance="Бір минут... сіз не айттыңыз?",
    body_language="looks up slowly, expression neutral",
    suggested_avatar_id="",
)

_DELTA_KEYS = {"trust", "fear", "anger", "hope"}
_DELTA_CLAMP = 30


def _build_user_prompt(
    intent: Intent,
    validation: ValidationResult,
    brief: ScenarioBriefData,
    current_emotion: dict,
    recent_memory: list,
) -> str:
    npc = brief.npc_definition
    memory_lines = []
    for m in recent_memory[-3:]:
        memory_lines.append(
            f"  Turn {m.turn_index}: user did '{m.user_intent_summary}'; "
            f"NPC said '{m.npc_response_summary}'"
        )

    return "\n".join([
        "## npc_persona",
        json.dumps(npc.to_dict(), ensure_ascii=False),
        "",
        "## npc_state",
        json.dumps({
            "emotion": current_emotion,
            "current_label": "unknown",
        }, ensure_ascii=False),
        "",
        "## npc_memory (last 3 turns)",
        "\n".join(memory_lines) or "(no memory yet — first turn)",
        "",
        "## intent",
        json.dumps(intent.to_dict(), ensure_ascii=False),
        "",
        "## validation",
        json.dumps({
            "is_legal": validation.is_legal,
            "is_standard_of_care": validation.is_standard_of_care,
            "severity_if_wrong": validation.severity_if_wrong,
            "blocks_action": validation.blocks_action,
            "coach_note": validation.coach_note,
        }, ensure_ascii=False),
        "",
        f"## locale\n{brief.locale}",
    ])


def _clamp_delta(v: object) -> int:
    try:
        return max(-_DELTA_CLAMP, min(_DELTA_CLAMP, int(float(v))))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _parse_npc_update(data: dict) -> NPCUpdate:
    raw_delta = data.get("emotion_delta") or {}
    emotion_delta = {k: _clamp_delta(raw_delta.get(k, 0)) for k in _DELTA_KEYS}
    return NPCUpdate(
        emotion_delta=emotion_delta,
        relationship_delta=_clamp_delta(data.get("relationship_delta", 0)),
        new_state_label=str(data.get("new_state_label", "calm_engaged")).strip(),
        utterance=str(data.get("utterance", "")).strip(),
        body_language=str(data.get("body_language", "")).strip(),
        suggested_avatar_id=str(data.get("suggested_avatar_id", "")).strip(),
    )


class NPCDirector:

    async def react(
        self,
        intent: Intent,
        validation: ValidationResult,
        brief: ScenarioBriefData,
        current_emotion: dict,
        recent_memory: list,
    ) -> NPCUpdate:
        system = _PROMPT_PATH.read_text(encoding="utf-8")
        user = _build_user_prompt(intent, validation, brief, current_emotion, recent_memory)
        try:
            data = await call_groq_json(
                system_prompt=system,
                user_prompt=user,
                max_tokens=280,
                temperature=0.7,
                schema_hint="NPCUpdate",
            )
            result = _parse_npc_update(data)
            logger.info(
                "npc_reacted",
                label=result.new_state_label,
                rel_delta=result.relationship_delta,
            )
            return result
        except Exception as e:
            logger.warning("npc_director_fallback", error=str(e))
            return _NEUTRAL_FALLBACK
