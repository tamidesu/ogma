"""
Open-world simulation API:

  POST /open-world/sessions                       — start an open-world session from a brief
  POST /open-world/sessions/{session_id}/turn     — process one free-text turn (SSE stream)
  GET  /open-world/sessions/{session_id}/state    — current world state + NPC state
  GET  /open-world/sessions/{session_id}/suggested-actions  — 4 AI-generated chips

SSE event sequence per turn (UPGRADE_PLAN §8.2):
  intent → validation → npc → world → scene → [terminal] → done
  mentor feedback is kicked off as a BackgroundTask after 'done'.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

import structlog
from fastapi import APIRouter, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.schemas.common import ResponseEnvelope
from app.agents.brief_loader import load_from_db
from app.agents.orchestrator import TurnOrchestrator
from app.agents.schemas import UserAction
from app.core.exceptions import NotFoundError, ValidationError
from app.db.models.profession import Profession
from app.db.models.scenario_brief import ScenarioBrief
from app.db.models.sim_session import SimulationSession
from app.db.repositories.open_world_repo import OpenWorldRepo
from app.dependencies import CurrentUser, DBSession

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/open-world", tags=["open-world"])

# Module-level orchestrator (stateless apart from agent instances)
_orchestrator = TurnOrchestrator()
_repo = OpenWorldRepo()


# ── Start session ─────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=ResponseEnvelope[dict], status_code=201)
async def create_open_world_session(
    body: dict,
    db: DBSession,
    current_user: CurrentUser,
):
    """
    Body: {"brief_id": "<uuid>"}
    Returns: session_id, initial world state, NPC initial utterance, case_file_md,
             suggested_actions (first 4 from brief).
    """
    brief_id_raw = body.get("brief_id")
    if not brief_id_raw:
        raise ValidationError("brief_id is required")
    try:
        brief_id = uuid.UUID(str(brief_id_raw))
    except ValueError:
        raise ValidationError("brief_id must be a valid UUID")

    # Load brief
    brief = await load_from_db(brief_id, db)
    if brief is None:
        raise NotFoundError("Brief not found")

    # Create session row
    session = SimulationSession(
        id=uuid.uuid4(),
        user_id=current_user.id,
        scenario_id=uuid.uuid4(),  # placeholder — not used in open-world
        brief_id=brief_id,
        mode="open_world",
        status="active",
        current_step_key="open_world",
        state_snapshot={},
        metrics=dict(brief.initial_world_state.get("metrics", {})),
        started_at=datetime.now(timezone.utc),
        last_active_at=datetime.now(timezone.utc),
    )
    db.add(session)

    # Write initial world state snapshot (turn_index = -1 marks "before turn 0")
    await _repo.write_world_snapshot(
        session_id=session.id,
        turn_index=-1,
        state=brief.initial_world_state,
        db=db,
    )
    await db.commit()

    logger.info(
        "open_world_session_created",
        session_id=str(session.id),
        brief_slug=brief.slug,
        user_id=str(current_user.id),
    )

    return ResponseEnvelope.ok({
        "session_id": str(session.id),
        "brief_id": str(brief_id),
        "brief_slug": brief.slug,
        "title": brief.title,
        "case_file_md": brief.case_file_md,
        "locale": brief.locale,
        "max_turns": brief.max_turns,
        "npc": {
            "id": brief.npc_definition.id,
            "display_name": brief.npc_definition.display_name,
            "role": brief.npc_definition.role,
            "initial_emotion": brief.npc_definition.initial_emotion,
            "avatar_image_id": brief.npc_definition.avatar_image_id,
        },
        "initial_world_state": brief.initial_world_state,
        "initial_suggested_actions": brief.initial_suggested_actions,
        "started_at": session.started_at.isoformat(),
    })


# ── Process turn (SSE) ────────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/turn")
async def process_turn(
    session_id: uuid.UUID,
    body: dict,
    db: DBSession,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    """
    Body: {"user_text": "...", "locale": "kk"}
    Returns: text/event-stream with events: intent, validation, npc, world, scene,
             [terminal], done.
    """
    user_text = (body.get("user_text") or "").strip()
    if not user_text:
        raise ValidationError("user_text is required")
    locale = str(body.get("locale") or "kk")

    # Verify session belongs to this user
    result = await db.execute(
        select(SimulationSession).where(
            SimulationSession.id == session_id,
            SimulationSession.user_id == current_user.id,
        )
    )
    sim_session = result.scalar_one_or_none()
    if sim_session is None:
        raise NotFoundError("Session not found")
    if sim_session.status not in ("active",):
        raise ValidationError(f"Session is {sim_session.status}, cannot process turn")

    # Load brief
    if sim_session.brief_id is None:
        raise ValidationError("This session is not an open-world session")
    brief = await load_from_db(sim_session.brief_id, db)
    if brief is None:
        raise NotFoundError("Brief not found")

    action = UserAction(raw_text=user_text, locale=locale)

    # Get redis for lock
    try:
        from app.db.redis import get_redis
        redis_client = await get_redis()
    except Exception:
        redis_client = None

    async def event_generator() -> AsyncGenerator[str, None]:
        turn_result = None
        turn_id = None
        turn_index = None

        try:
            gen = await _orchestrator.run_turn(
                session_id=session_id,
                action=action,
                brief=brief,
                db=db,
                redis_client=redis_client,
            )
            async for event_name, payload in gen:
                data = json.dumps(payload, ensure_ascii=False, default=str)
                yield f"event: {event_name}\ndata: {data}\n\n"
                if event_name == "done":
                    turn_id = _orchestrator._last_turn_id
                    turn_index = _orchestrator._last_turn_index
                    turn_result = getattr(_orchestrator, "_last_turn_result", None)
        except Exception as e:
            logger.error("turn_sse_error", error=str(e), session_id=str(session_id))
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
            return

        # Schedule mentor coach as background task
        if turn_result is not None:
            background_tasks.add_task(
                _run_mentor_coach,
                turn_result=turn_result,
                brief=brief,
                session_id=session_id,
                turn_index=turn_index or 0,
                user_input=user_text,
                turn_id=turn_id,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def _run_mentor_coach(
    turn_result,
    brief,
    session_id: uuid.UUID,
    turn_index: int,
    user_input: str,
    turn_id: uuid.UUID | None,
):
    """Background task: generate mentor feedback and link it to the turn row."""
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        coach = _orchestrator._mentor
        feedback_id = await coach.generate(
            turn=turn_result,
            brief=brief,
            session_id=session_id,
            turn_index=turn_index,
            user_input=user_input,
            db=db,
        )
        if feedback_id and turn_id:
            await _repo.set_mentor_feedback_id(turn_id, feedback_id, db)
            await db.commit()


# ── Session state ─────────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/state", response_model=ResponseEnvelope[dict])
async def get_session_state(
    session_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(SimulationSession).where(
            SimulationSession.id == session_id,
            SimulationSession.user_id == current_user.id,
        )
    )
    sim_session = result.scalar_one_or_none()
    if not sim_session:
        raise NotFoundError("Session not found")

    world_state = await _repo.get_latest_world_state(session_id, db)
    npc_state = await _repo.get_npc_state(session_id, db)
    turn_index = await _repo.next_turn_index(session_id, db)

    return ResponseEnvelope.ok({
        "session_id": str(session_id),
        "status": sim_session.status,
        "turn_index": turn_index,
        "world_state": world_state,
        "npc_state": npc_state,
    })


# ── Suggested actions ─────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/suggested-actions", response_model=ResponseEnvelope[list[str]])
async def get_suggested_actions(
    session_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """
    Returns 4 action chip suggestions for the current world state.
    Turn 0: returns the brief's hand-authored initial_suggested_actions.
    Later turns: LLM-generated based on current world state.
    Results are Redis-cached for 60s keyed by state hash.
    """
    result = await db.execute(
        select(SimulationSession).where(
            SimulationSession.id == session_id,
            SimulationSession.user_id == current_user.id,
        )
    )
    sim_session = result.scalar_one_or_none()
    if not sim_session or not sim_session.brief_id:
        raise NotFoundError("Session not found or not an open-world session")

    brief = await load_from_db(sim_session.brief_id, db)
    if not brief:
        raise NotFoundError("Brief not found")

    turn_count = await _repo.next_turn_index(session_id, db)

    if turn_count == 0:
        return ResponseEnvelope.ok(brief.initial_suggested_actions[:4])

    # For subsequent turns: check Redis cache, then generate
    world_state = await _repo.get_latest_world_state(session_id, db)

    try:
        from app.db.redis import get_redis
        redis = await get_redis()
        import hashlib, json as _json
        state_hash = hashlib.sha1(
            _json.dumps(world_state, sort_keys=True, ensure_ascii=False, default=str).encode()
        ).hexdigest()[:16]
        cache_key = f"suggestions:{session_id}:{state_hash}"
        cached = await redis.get(cache_key)
        if cached:
            return ResponseEnvelope.ok(_json.loads(cached))
    except Exception:
        redis = None
        cache_key = None

    suggestions = await _generate_suggestions(brief, world_state)

    if redis and cache_key:
        try:
            import json as _json2
            await redis.set(cache_key, _json2.dumps(suggestions, ensure_ascii=False), ex=60)
        except Exception:
            pass

    return ResponseEnvelope.ok(suggestions)


async def _generate_suggestions(brief, world_state: dict | None) -> list[str]:
    """One cheap LLM call for 4 action suggestions."""
    from app.agents.groq_helper import call_groq_json

    system = (
        "You generate exactly 4 short (5-10 word) action suggestions for a simulation trainee. "
        f"Profession: {brief.profession_slug}. "
        f"NPC: {brief.npc_definition.display_name} ({brief.npc_definition.role}). "
        f"Locale: {brief.locale}. "
        "Return JSON: {\"suggestions\": [\"...\", \"...\", \"...\", \"...\"]}"
    )
    user = (
        f"Current phase: {(world_state or {}).get('time', {}).get('current_phase', 'unknown')}\n"
        f"Metrics: {(world_state or {}).get('metrics', {})}\n"
        f"Active flags: {[k for k,v in ((world_state or {}).get('flags') or {}).items() if v is True]}"
    )
    try:
        data = await call_groq_json(
            system_prompt=system,
            user_prompt=user,
            max_tokens=150,
            temperature=0.5,
            schema_hint="Suggestions",
        )
        suggestions = data.get("suggestions") or []
        return [str(s) for s in suggestions[:4]]
    except Exception:
        return brief.initial_suggested_actions[:4]
