from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.sim_session import SimulationSession
from app.db.models.decision_log import DecisionLog
from app.simulation.models.session_state import SimSessionState


class SessionRepository:

    async def get_by_id(self, session_id: UUID, db: AsyncSession) -> SimulationSession | None:
        result = await db.execute(
            select(SimulationSession).where(SimulationSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_active_for_user(
        self, user_id: UUID, scenario_id: UUID, db: AsyncSession
    ) -> SimulationSession | None:
        result = await db.execute(
            select(SimulationSession).where(
                SimulationSession.user_id == user_id,
                SimulationSession.scenario_id == scenario_id,
                SimulationSession.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: UUID,
        db: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> list[SimulationSession]:
        result = await db.execute(
            select(SimulationSession)
            .where(SimulationSession.user_id == user_id)
            .order_by(SimulationSession.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def create(
        self,
        user_id: UUID,
        scenario_id: UUID,
        state: SimSessionState,
        db: AsyncSession,
    ) -> SimulationSession:
        now = datetime.now(timezone.utc)
        sim_session = SimulationSession(
            user_id=user_id,
            scenario_id=scenario_id,
            scenario_version=state.scenario_version,
            status="active",
            current_step_key=state.current_step_key,
            state_snapshot=state.to_dict(),
            metrics=state.metrics.to_dict(),
            started_at=now,
            last_active_at=now,
        )
        db.add(sim_session)
        await db.flush()
        await db.refresh(sim_session)
        return sim_session

    async def update_state(
        self,
        sim_session: SimulationSession,
        state: SimSessionState,
        db: AsyncSession,
    ) -> SimulationSession:
        sim_session.current_step_key = state.current_step_key
        sim_session.state_snapshot = state.to_dict()
        sim_session.metrics = state.metrics.to_dict()
        sim_session.last_active_at = datetime.now(timezone.utc)
        await db.flush()
        return sim_session

    async def complete(
        self,
        sim_session: SimulationSession,
        final_score: float,
        db: AsyncSession,
    ) -> SimulationSession:
        now = datetime.now(timezone.utc)
        sim_session.status = "completed"
        sim_session.completed_at = now
        sim_session.final_score = final_score
        sim_session.last_active_at = now
        await db.flush()
        return sim_session

    async def set_status(
        self, sim_session: SimulationSession, status: str, db: AsyncSession
    ) -> SimulationSession:
        sim_session.status = status
        sim_session.last_active_at = datetime.now(timezone.utc)
        await db.flush()
        return sim_session

    async def log_decision(
        self,
        session_id: UUID,
        step_key: str,
        option_key: str,
        effects_applied: list,
        metrics_before: dict,
        metrics_after: dict,
        state_before: dict,
        state_after: dict,
        decided_at: datetime,
        time_spent_sec: int | None,
        db: AsyncSession,
    ) -> DecisionLog:
        log = DecisionLog(
            session_id=session_id,
            step_key=step_key,
            option_key=option_key,
            effects_applied=effects_applied,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            state_before=state_before,
            state_after=state_after,
            decided_at=decided_at,
            time_spent_sec=time_spent_sec,
        )
        db.add(log)
        await db.flush()
        await db.refresh(log)
        return log

    async def attach_feedback(
        self,
        log_id: UUID,
        feedback_id: UUID,
        db: AsyncSession,
    ) -> None:
        await db.execute(
            update(DecisionLog)
            .where(DecisionLog.id == log_id)
            .values(ai_feedback_id=feedback_id)
        )

    async def get_history(
        self,
        session_id: UUID,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DecisionLog]:
        result = await db.execute(
            select(DecisionLog)
            .where(DecisionLog.session_id == session_id)
            .order_by(DecisionLog.decided_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
