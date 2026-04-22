import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.schemas.common import ResponseEnvelope
from app.api.schemas.simulation import (
    CreateSessionRequest, DecisionHistoryItem, DecisionResponse,
    MakeDecisionRequest, OptionInfo, SessionResponse, SessionSummaryResponse, StepInfo,
    AIFeedbackResponse, FeedbackPollResponse,
)
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.db.models.decision_log import DecisionLog
from app.db.models.ai_feedback import AIFeedback
from app.db.repositories.session_repo import SessionRepository
from app.dependencies import CurrentUser, DBSession
from app.services.decision_service import DecisionService
from app.services.session_service import SessionService
from app.simulation.engine import SimulationEngine
from app.simulation.loader import ScenarioLoader

router = APIRouter(prefix="/sessions", tags=["sessions"])
session_service = SessionService()
decision_service = DecisionService()
session_repo = SessionRepository()
engine = SimulationEngine()
loader = ScenarioLoader()


def _feedback_response(fb: AIFeedback) -> AIFeedbackResponse:
    return AIFeedbackResponse(
        text=fb.feedback_text,
        generated=True,
        tone=fb.tone,
        key_insight=fb.key_insight,
        coaching_question=fb.coaching_question,
        consequence_analysis=fb.consequence_analysis,
        alternative_path=fb.alternative_path,
    )


@router.post("", response_model=ResponseEnvelope[SessionResponse], status_code=201)
async def create_session(
    body: CreateSessionRequest,
    db: DBSession,
    current_user: CurrentUser,
):
    sim_session, state = await session_service.create_session(
        current_user.id, body.scenario_id, db
    )
    scenario = await loader.load(sim_session.scenario_id, db)
    current_step = scenario.get_step(state.current_step_key)
    available_options = engine.get_available_options(state, scenario)

    return ResponseEnvelope.ok(SessionResponse(
        session_id=str(sim_session.id),
        status=sim_session.status,
        scenario_id=str(sim_session.scenario_id),
        current_step=StepInfo(
            step_key=current_step.step_key,
            title=current_step.title,
            narrative=current_step.narrative,
            step_type=current_step.step_type.value,
            available_options=[OptionInfo(**o) for o in available_options],
        ) if current_step else None,
        metrics=state.metrics.to_dict(),
        step_count=state.step_count,
        started_at=sim_session.started_at.isoformat(),
    ))


@router.get("/{session_id}", response_model=ResponseEnvelope[SessionResponse])
async def get_session(session_id: UUID, db: DBSession, current_user: CurrentUser):
    sim_session, state = await session_service.load_session(session_id, current_user.id, db)
    scenario = await loader.load(sim_session.scenario_id, db)
    current_step = scenario.get_step(state.current_step_key)
    available_options = engine.get_available_options(state, scenario) if current_step else []

    return ResponseEnvelope.ok(SessionResponse(
        session_id=str(sim_session.id),
        status=sim_session.status,
        scenario_id=str(sim_session.scenario_id),
        current_step=StepInfo(
            step_key=current_step.step_key,
            title=current_step.title,
            narrative=current_step.narrative,
            step_type=current_step.step_type.value,
            available_options=[OptionInfo(**o) for o in available_options],
        ) if current_step else None,
        metrics=state.metrics.to_dict(),
        step_count=state.step_count,
        started_at=sim_session.started_at.isoformat(),
    ))


@router.post("/{session_id}/decisions", response_model=ResponseEnvelope[DecisionResponse])
async def make_decision(
    session_id: UUID,
    body: MakeDecisionRequest,
    db: DBSession,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    result = await decision_service.process(
        session_id=session_id,
        option_key=body.option_key,
        user_id=current_user.id,
        db=db,
        background_tasks=background_tasks,
        time_spent_sec=body.time_spent_sec,
    )
    # Map next_step dict to StepInfo
    if result.get("next_step"):
        ns = result["next_step"]
        result["next_step"] = StepInfo(
            step_key=ns["step_key"],
            title=ns["title"],
            narrative=ns["narrative"],
            step_type=ns["step_type"],
            available_options=[OptionInfo(**o) for o in ns.get("available_options", [])],
        )
    result["ai_feedback"] = AIFeedbackResponse(**result["ai_feedback"])
    return ResponseEnvelope.ok(DecisionResponse(**result))


@router.post("/{session_id}/pause", response_model=ResponseEnvelope[dict])
async def pause_session(session_id: UUID, db: DBSession, current_user: CurrentUser):
    await session_service.pause_session(session_id, current_user.id, db)
    return ResponseEnvelope.ok({"status": "paused"})


@router.delete("/{session_id}", status_code=204)
async def abandon_session(session_id: UUID, db: DBSession, current_user: CurrentUser):
    await session_service.abandon_session(session_id, current_user.id, db)


@router.get("/{session_id}/history", response_model=ResponseEnvelope[list[DecisionHistoryItem]])
async def get_history(
    session_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
):
    sim_session, _ = await session_service.load_session(session_id, current_user.id, db)
    logs = await session_repo.get_history(session_id, db, limit=limit, offset=offset)

    items = []
    for log in logs:
        # Fetch feedback if linked
        feedback_resp = None
        if log.ai_feedback_id:
            result = await db.execute(
                select(AIFeedback).where(AIFeedback.id == log.ai_feedback_id)
            )
            fb = result.scalar_one_or_none()
            if fb:
                feedback_resp = _feedback_response(fb)
        items.append(DecisionHistoryItem(
            id=str(log.id),
            step_key=log.step_key,
            option_key=log.option_key,
            metrics_before=log.metrics_before,
            metrics_after=log.metrics_after,
            effects_applied=log.effects_applied,
            decided_at=log.decided_at.isoformat(),
            time_spent_sec=log.time_spent_sec,
            ai_feedback=feedback_resp,
        ))

    return ResponseEnvelope.ok(items)


@router.get("/{session_id}/decisions/{decision_id}/feedback", response_model=ResponseEnvelope[FeedbackPollResponse])
async def poll_feedback(
    session_id: UUID,
    decision_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """Frontend polls this after making a decision to get AI feedback when ready."""
    # Verify session ownership
    await session_service.load_session(session_id, current_user.id, db)

    result = await db.execute(
        select(DecisionLog).where(
            DecisionLog.id == decision_id,
            DecisionLog.session_id == session_id,
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        raise NotFoundError("Decision", str(decision_id))

    if log.ai_feedback_id:
        fb_result = await db.execute(
            select(AIFeedback).where(AIFeedback.id == log.ai_feedback_id)
        )
        fb = fb_result.scalar_one_or_none()
        if fb:
            return ResponseEnvelope.ok(FeedbackPollResponse(
                decision_id=str(decision_id),
                ready=True,
                feedback=_feedback_response(fb),
            ))

    return ResponseEnvelope.ok(FeedbackPollResponse(
        decision_id=str(decision_id), ready=False, feedback=None
    ))


@router.get("/{session_id}/decisions/{decision_id}/feedback/stream")
async def stream_feedback(
    session_id: UUID,
    decision_id: UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    """
    SSE stream for AI feedback on a decision.
    Polls DB every second until feedback is ready, then streams field-by-field as SSE events.
    Events: data: {"event": "ready", "feedback": {...}} on success,
            data: {"event": "pending"} while waiting,
            data: {"event": "not_found"} if decision doesn't belong to session.
    """
    await session_service.load_session(session_id, current_user.id, db)

    result = await db.execute(
        select(DecisionLog).where(
            DecisionLog.id == decision_id,
            DecisionLog.session_id == session_id,
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        async def _not_found():
            yield f"data: {json.dumps({'event': 'not_found'})}\n\n"
        return StreamingResponse(_not_found(), media_type="text/event-stream")

    async def _sse_generator():
        from app.db.session import async_session_factory
        max_wait_sec = 30
        poll_interval = 1.0
        elapsed = 0.0

        while elapsed < max_wait_sec:
            async with async_session_factory() as poll_db:
                log_result = await poll_db.execute(
                    select(DecisionLog).where(DecisionLog.id == decision_id)
                )
                poll_log = log_result.scalar_one_or_none()
                if poll_log and poll_log.ai_feedback_id:
                    fb_result = await poll_db.execute(
                        select(AIFeedback).where(AIFeedback.id == poll_log.ai_feedback_id)
                    )
                    fb = fb_result.scalar_one_or_none()
                    if fb:
                        payload = {
                            "event": "ready",
                            "feedback": {
                                "text": fb.feedback_text,
                                "generated": True,
                                "tone": fb.tone,
                                "key_insight": fb.key_insight,
                                "coaching_question": fb.coaching_question,
                                "consequence_analysis": fb.consequence_analysis,
                                "alternative_path": fb.alternative_path,
                            },
                        }
                        yield f"data: {json.dumps(payload)}\n\n"
                        return

            yield f"data: {json.dumps({'event': 'pending', 'elapsed': elapsed})}\n\n"
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        yield f"data: {json.dumps({'event': 'timeout'})}\n\n"

    return StreamingResponse(_sse_generator(), media_type="text/event-stream")
