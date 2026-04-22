from fastapi import APIRouter, Query
from sqlalchemy import select, func

from app.api.schemas.common import ResponseEnvelope
from app.api.schemas.simulation import ProgressResponse, SessionSummaryResponse, SkillScoreItem
from app.db.models.sim_session import SimulationSession
from app.db.repositories.session_repo import SessionRepository
from app.dependencies import CurrentUser, DBSession
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/users/me", tags=["progress"])
progress_service = ProgressService()
session_repo = SessionRepository()


@router.get("/progress", response_model=ResponseEnvelope[ProgressResponse])
async def get_progress(db: DBSession, current_user: CurrentUser):
    summary = await progress_service.get_progress_summary(current_user.id, db)
    return ResponseEnvelope.ok(ProgressResponse(
        level=summary["level"],
        xp_total=summary["xp_total"],
        xp_to_next_level=summary["xp_to_next_level"],
        skill_scores=[SkillScoreItem(**s) for s in summary["skill_scores"]],
        scenarios_completed=summary["scenarios_completed"],
    ))


@router.get("/sessions", response_model=ResponseEnvelope[list[SessionSummaryResponse]])
async def list_sessions(
    db: DBSession,
    current_user: CurrentUser,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
):
    sessions = await session_repo.list_for_user(current_user.id, db, limit=limit, offset=offset)
    return ResponseEnvelope.ok([
        SessionSummaryResponse(
            session_id=str(s.id),
            scenario_id=str(s.scenario_id),
            status=s.status,
            final_score=float(s.final_score) if s.final_score else None,
            started_at=s.started_at.isoformat(),
            completed_at=s.completed_at.isoformat() if s.completed_at else None,
        )
        for s in sessions
    ])
