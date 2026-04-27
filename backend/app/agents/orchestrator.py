"""
TurnOrchestrator — runs the full agent pipeline for one open-world turn.

Sequencing (UPGRADE_PLAN §3.3):
  1. ActionInterpreter       -> structured intent
  2. DomainValidator (RAG)   -> legality / SoC / citations
     * if blocks_action:  NPC reacts to refusal; world unchanged; turn recorded
  3. NPCDirector + ConsequenceEngine in parallel (asyncio.gather)
  4. Apply world-state delta -> new world state
  5. Evaluate success/failure criteria
  6. VisualDirector          -> picks image
  7. Persist: AgentTurn, WorldStateSnapshot, NPCState (under Redis lock)
  8. Schedule MentorCoach as BackgroundTask
  9. Yield SSE events to the API layer

Each agent's output is yielded as an SSE event the moment it's ready.
Redis lock (turn:lock:{session_id}, TTL 30s) prevents concurrent turns.
On any agent error -> safe fallback (verb=clarify, world unchanged).
"""
from __future__ import annotations

import asyncio
import copy
import time
from typing import Any, AsyncGenerator
from uuid import UUID

import structlog

from app.agents.action_interpreter import ActionInterpreter
from app.agents.consequence_engine import ConsequenceEngine
from app.agents.domain_validator import DomainValidator
from app.agents.image_library import get_library
from app.agents.mentor_coach import MentorCoach
from app.agents.npc_director import NPCDirector
from app.agents.schemas import (
    ImageMatch, Intent, NPCMemoryItem, NPCUpdate,
    ScenarioBriefData, TurnResult, UserAction, ValidationResult, WorldDelta,
)
from app.agents.visual_director import VisualDirector
from app.db.repositories.open_world_repo import OpenWorldRepo

logger = structlog.get_logger(__name__)

# ── safe fallbacks ────────────────────────────────────────────────────────────

_SAFE_NPC = NPCUpdate(
    emotion_delta={"trust": 0, "fear": 0, "anger": 0, "hope": 0},
    relationship_delta=0,
    new_state_label="calm_engaged",
    utterance="Бір секунд... сіз не айттыңыз?",
    body_language="pauses, looks up slowly",
    suggested_avatar_id="",
)

_SAFE_DELTA = WorldDelta(
    metric_delta={},
    state_set={},
    time_advance_min=0,
    new_complication=None,
    skill_xp=[],
)

_BLOCKED_NPC = NPCUpdate(
    emotion_delta={"trust": -10, "fear": 15, "anger": 5, "hope": -5},
    relationship_delta=-3,
    new_state_label="anxious_distressed",
    utterance="Бұл... мүмкін емес, солай ма? Не болып жатыр?",
    body_language="grips the chair arm tightly, looks between the doctor and the door",
    suggested_avatar_id="",
)


def _clamp_emotion(emotion: dict, delta: dict) -> dict:
    result = dict(emotion)
    for k, v in delta.items():
        result[k] = max(0, min(100, result.get(k, 50) + v))
    return result


def _apply_world_delta(world_state: dict, delta: WorldDelta) -> dict:
    """Return a new world state with the delta applied. Does not mutate inputs."""
    state = copy.deepcopy(world_state)

    metrics = state.setdefault("metrics", {})
    for k, v in delta.metric_delta.items():
        metrics[k] = max(0.0, min(100.0, metrics.get(k, 0) + v))

    for dotted_key, value in delta.state_set.items():
        parts = dotted_key.split(".", 1)
        if len(parts) == 2:
            bucket, key = parts
            state.setdefault(bucket, {})[key] = value
        else:
            state[dotted_key] = value

    time_bucket = state.setdefault("time", {})
    time_bucket["elapsed_min"] = time_bucket.get("elapsed_min", 0) + delta.time_advance_min

    if delta.new_complication and isinstance(delta.new_complication.get("metric_delta"), dict):
        for k, v in delta.new_complication["metric_delta"].items():
            metrics[k] = max(0.0, min(100.0, metrics.get(k, 0) + v))

    return state


def _evaluate_criteria(criteria: dict | None, world_state: dict) -> bool:
    if not criteria:
        return False
    try:
        return _jsonlogic(criteria, world_state)
    except Exception:
        return False


def _jsonlogic(logic: dict, data: dict) -> bool:  # noqa: C901
    """Evaluate a minimal JsonLogic subset against a nested dict."""
    if not isinstance(logic, dict) or not logic:
        return bool(logic)
    op, args = next(iter(logic.items()))
    if op == "and":
        return all(_jsonlogic(a, data) for a in args)
    if op == "or":
        return any(_jsonlogic(a, data) for a in args)
    if op == "!":
        return not _jsonlogic(args, data)

    def _resolve(v: Any) -> Any:
        if isinstance(v, dict) and "var" in v:
            path = v["var"]
            node = data
            for part in path.split("."):
                if not isinstance(node, dict):
                    return None
                node = node.get(part)
            return node
        if isinstance(v, dict):
            return _jsonlogic(v, data)
        return v

    a, b = _resolve(args[0]), _resolve(args[1])
    try:
        if op == "==":
            return a == b
        if op == "!=":
            return a != b
        if op == ">=":
            return float(a) >= float(b)
        if op == "<=":
            return float(a) <= float(b)
        if op == ">":
            return float(a) > float(b)
        if op == "<":
            return float(a) < float(b)
    except (TypeError, ValueError):
        return False
    return False


class TurnOrchestrator:
    LOCK_TTL_SEC = 30
    LOCK_KEY_FMT = "turn:lock:{session_id}"
    NPC_MEMORY_CAP = 12

    def __init__(self):
        self._interpreter = ActionInterpreter()
        self._validator = DomainValidator()
        self._npc_director = NPCDirector()
        self._consequence = ConsequenceEngine()
        self._visual = VisualDirector(library=get_library())
        self._mentor = MentorCoach()
        self._repo = OpenWorldRepo()

    async def run_turn(
        self,
        session_id: UUID,
        action: UserAction,
        brief: ScenarioBriefData,
        db,
        redis_client=None,
    ) -> AsyncGenerator[tuple[str, dict], None]:
        return self._pipeline(session_id, action, brief, db, redis_client)

    async def _pipeline(
        self,
        session_id: UUID,
        action: UserAction,
        brief: ScenarioBriefData,
        db,
        redis_client,
    ) -> AsyncGenerator[tuple[str, dict], None]:
        start_ms = time.monotonic()

        lock_key = self.LOCK_KEY_FMT.format(session_id=session_id)
        if redis_client:
            locked = await redis_client.set(
                lock_key, "1", nx=True, ex=self.LOCK_TTL_SEC
            )
            if not locked:
                yield "error", {"code": "TURN_IN_PROGRESS",
                                 "message": "Another turn is already being processed."}
                return
        try:
            async for event in self._run_agents(
                session_id, action, brief, db, redis_client, start_ms
            ):
                yield event
        finally:
            if redis_client:
                await redis_client.delete(lock_key)

    async def _run_agents(   # noqa: C901
        self,
        session_id: UUID,
        action: UserAction,
        brief: ScenarioBriefData,
        db,
        redis_client,
        start_ms: float,
    ) -> AsyncGenerator[tuple[str, dict], None]:

        # ── 1. Load session state ─────────────────────────────────────
        world_state = await self._repo.get_latest_world_state(session_id, db)
        if world_state is None:
            world_state = copy.deepcopy(brief.initial_world_state)

        npc_state_row = await self._repo.get_npc_state(session_id, db)
        if npc_state_row is None:
            npc_def = brief.npc_definition
            current_emotion: dict = dict(npc_def.initial_emotion)
            relationship_score: int = 0
            memory: list = []
            current_label: str | None = None
        else:
            current_emotion = dict(npc_state_row["emotion"])
            relationship_score = int(npc_state_row["relationship_score"])
            memory = list(npc_state_row["memory"])
            current_label = npc_state_row.get("current_label")

        turn_index = await self._repo.next_turn_index(session_id, db)

        history_summary = " -> ".join(
            m.get("user_intent_summary", "") for m in memory[-3:]
        )

        # ── 2. ActionInterpreter ──────────────────────────────────────
        intent: Intent = await self._interpreter.interpret(
            action=action,
            brief=brief,
            recent_history_summary=history_summary,
        )
        yield "intent", {
            "verb": intent.verb,
            "target": intent.target,
            "plausibility": intent.plausibility,
            "requires_clarification": intent.requires_clarification,
            "raw_paraphrase": intent.raw_paraphrase,
        }

        # ── 3. DomainValidator ────────────────────────────────────────
        validation: ValidationResult = await self._validator.validate(
            intent=intent,
            brief=brief,
            world_state=world_state,
        )
        yield "validation", {
            "is_legal": validation.is_legal,
            "is_standard_of_care": validation.is_standard_of_care,
            "severity_if_wrong": validation.severity_if_wrong,
            "citations": [c.to_dict() for c in validation.citations],
            "coach_note": validation.coach_note,
            "blocks_action": validation.blocks_action,
        }

        # ── 3b. Short-circuit on blocked action ───────────────────────
        if validation.blocks_action:
            npc_update = _BLOCKED_NPC
            world_delta = _SAFE_DELTA
            new_world_state = world_state
        else:
            # ── 4. NPCDirector + ConsequenceEngine in parallel ────────
            recent_memory_items = [
                NPCMemoryItem(
                    turn_index=m.get("turn_index", i),
                    user_intent_summary=m.get("user_intent_summary", ""),
                    npc_response_summary=m.get("npc_response_summary", ""),
                    emotion_at_time=m.get("emotion_at_time", {}),
                )
                for i, m in enumerate(memory[-3:])
            ]
            npc_update, world_delta = await asyncio.gather(
                self._npc_director.react(
                    intent=intent,
                    validation=validation,
                    brief=brief,
                    current_emotion=current_emotion,
                    recent_memory=recent_memory_items,
                ),
                self._consequence.resolve(
                    intent=intent,
                    validation=validation,
                    npc_update=_SAFE_NPC,
                    brief=brief,
                    world_state=world_state,
                    turn_index=turn_index,
                ),
            )
            new_world_state = _apply_world_delta(world_state, world_delta)

        # ── 5. Emit NPC event ─────────────────────────────────────────
        yield "npc", {
            "emotion_delta": npc_update.emotion_delta,
            "new_state_label": npc_update.new_state_label,
            "utterance": npc_update.utterance,
            "body_language": npc_update.body_language,
            "suggested_avatar_id": npc_update.suggested_avatar_id,
            "relationship_delta": npc_update.relationship_delta,
        }

        # ── 6. Emit world event ───────────────────────────────────────
        new_metrics = new_world_state.get("metrics", {})
        yield "world", {
            "metric_delta": world_delta.metric_delta,
            "state_set": world_delta.state_set,
            "time_advance_min": world_delta.time_advance_min,
            "new_complication": world_delta.new_complication,
            "skill_xp": [{"skill": g.skill, "xp": g.xp} for g in world_delta.skill_xp],
            "current_metrics": new_metrics,
            "elapsed_min": (new_world_state.get("time") or {}).get("elapsed_min", 0),
        }

        # ── 7. VisualDirector ─────────────────────────────────────────
        image: ImageMatch = await self._visual.pick(
            intent=intent,
            npc_update=npc_update,
            world_delta=world_delta,
            brief=brief,
            world_state_after=new_world_state,
        )
        yield "scene", {
            "image_id": image.image_id,
            "image_url": image.url,
            "alt_text": image.alt_text,
            "is_fallback": image.is_fallback,
            "transition": "crossfade",
        }

        # ── 8. Evaluate termination ───────────────────────────────────
        is_terminal = False
        termination_reason: str | None = None
        if _evaluate_criteria(brief.success_criteria_jsonlogic, new_world_state):
            is_terminal = True
            termination_reason = "success"
        elif _evaluate_criteria(brief.failure_criteria_jsonlogic, new_world_state):
            is_terminal = True
            termination_reason = "failure"
        elif turn_index + 1 >= brief.max_turns:
            is_terminal = True
            termination_reason = "timeout"

        # ── 9. Persist ────────────────────────────────────────────────
        new_emotion = _clamp_emotion(current_emotion, npc_update.emotion_delta)
        new_rel_score = max(-100, min(100, relationship_score + npc_update.relationship_delta))

        new_memory = list(memory) + [{
            "turn_index": turn_index,
            "user_intent_summary": intent.raw_paraphrase or f"{intent.verb} {intent.target}",
            "npc_response_summary": npc_update.utterance[:120] if npc_update.utterance else "",
            "emotion_at_time": new_emotion,
        }]
        if len(new_memory) > self.NPC_MEMORY_CAP:
            new_memory = new_memory[-self.NPC_MEMORY_CAP:]

        latency_ms = int((time.monotonic() - start_ms) * 1000)

        turn_result = TurnResult(
            intent=intent,
            validation=validation,
            npc_update=npc_update,
            world_delta=world_delta,
            image=image,
            is_terminal=is_terminal,
            termination_reason=termination_reason,
            pipeline_latency_ms=latency_ms,
        )

        turn_id = None
        try:
            turn_id = await self._repo.write_agent_turn(
                session_id=session_id,
                turn_index=turn_index,
                user_input=action.raw_text,
                locale=action.locale,
                intent_json=intent.to_dict(),
                validation_json=validation.to_dict(),
                npc_update_json=npc_update.to_dict(),
                world_delta_json=world_delta.to_dict(),
                image_id=image.image_id or None,
                is_terminal=is_terminal,
                termination_reason=termination_reason,
                pipeline_latency_ms=latency_ms,
                db=db,
            )
            await self._repo.write_world_snapshot(
                session_id=session_id,
                turn_index=turn_index,
                state=new_world_state,
                db=db,
            )
            await self._repo.upsert_npc_state(
                session_id=session_id,
                definition_id=brief.npc_definition.id,
                emotion=new_emotion,
                relationship_score=new_rel_score,
                memory=new_memory,
                current_label=npc_update.new_state_label,
                current_avatar_id=npc_update.suggested_avatar_id or None,
                db=db,
            )
            await db.commit()
        except Exception as e:
            logger.error("orchestrator_persist_failed", error=str(e), session_id=str(session_id))
            await db.rollback()

        # ── 10. Terminal event ────────────────────────────────────────
        if is_terminal:
            yield "terminal", {
                "is_terminal": True,
                "termination_reason": termination_reason,
                "final_metrics": new_metrics,
                "total_turns": turn_index + 1,
                "timeout_resolution": brief.timeout_resolution
                    if termination_reason == "timeout" else None,
            }

        # ── 11. Done ──────────────────────────────────────────────────
        yield "done", {
            "turn_index": turn_index,
            "latency_ms": latency_ms,
            "turn_id": str(turn_id) if turn_id is not None else None,
        }

        # Store for API layer to pick up for MentorCoach BackgroundTask
        self._last_turn_result = turn_result
        self._last_turn_id = turn_id
        self._last_turn_index = turn_index
