import json
from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import NotFoundError, PermissionDeniedError, SessionNotActiveError
from app.db.models.sim_session import SimulationSession
from app.db.redis import get_redis
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.scenario_repo import ScenarioRepository
from app.simulation.engine import SimulationEngine
from app.simulation.models.session_state import SimSessionState

logger = structlog.get_logger(__name__)
session_repo = SessionRepository()
scenario_repo = ScenarioRepository()
engine = SimulationEngine()

_CACHE_KEY = "session_state:{session_id}"


class SessionService:

    async def create_session(
        self,
        user_id: UUID,
        scenario_id: UUID,
        db: AsyncSession,
    ) -> tuple[SimulationSession, SimSessionState]:
        scenario_db = await scenario_repo.get_scenario(scenario_id, db)
        if not scenario_db or not scenario_db.is_published:
            raise NotFoundError("Scenario", str(scenario_id))

        state = await engine.build_initial_state(scenario_id, None, db)

        sim_session = await session_repo.create(user_id, scenario_id, state, db)
        # Bind real session ID into state
        state.session_id = sim_session.id

        await self._cache_state(sim_session.id, state)
        logger.info("session_created", session_id=str(sim_session.id), user_id=str(user_id))
        return sim_session, state

    async def load_session(
        self,
        session_id: UUID,
        user_id: UUID,
        db: AsyncSession,
    ) -> tuple[SimulationSession, SimSessionState]:
        sim_session = await session_repo.get_by_id(session_id, db)
        if not sim_session:
            raise NotFoundError("Session", str(session_id))
        if sim_session.user_id != user_id:
            raise PermissionDeniedError()

        # Try cache first
        state = await self._load_cached_state(session_id)
        if not state:
            state = SimSessionState.from_dict(sim_session.state_snapshot)
            await self._cache_state(session_id, state)

        return sim_session, state

    async def persist_state(
        self,
        sim_session: SimulationSession,
        state: SimSessionState,
        db: AsyncSession,
    ) -> None:
        await session_repo.update_state(sim_session, state, db)
        await self._cache_state(sim_session.id, state)

    async def complete_session(
        self,
        sim_session: SimulationSession,
        final_score: float,
        db: AsyncSession,
    ) -> SimulationSession:
        completed = await session_repo.complete(sim_session, final_score, db)
        await self._invalidate_cache(sim_session.id)
        logger.info("session_completed", session_id=str(sim_session.id), score=final_score)
        return completed

    async def pause_session(
        self, session_id: UUID, user_id: UUID, db: AsyncSession
    ) -> SimulationSession:
        sim_session, _ = await self.load_session(session_id, user_id, db)
        if sim_session.status != "active":
            raise SessionNotActiveError(sim_session.status)
        return await session_repo.set_status(sim_session, "paused", db)

    async def abandon_session(
        self, session_id: UUID, user_id: UUID, db: AsyncSession
    ) -> SimulationSession:
        sim_session, _ = await self.load_session(session_id, user_id, db)
        if sim_session.status in ("completed", "abandoned"):
            raise SessionNotActiveError(sim_session.status)
        await self._invalidate_cache(session_id)
        return await session_repo.set_status(sim_session, "abandoned", db)

    # ── Redis cache helpers ───────────────────────────────

    async def _cache_state(self, session_id: UUID, state: SimSessionState) -> None:
        try:
            redis = await get_redis()
            key = _CACHE_KEY.format(session_id=str(session_id))
            await redis.setex(key, settings.redis_session_ttl, json.dumps(state.to_dict()))
        except Exception:
            pass  # Cache failure is non-fatal

    async def _load_cached_state(self, session_id: UUID) -> SimSessionState | None:
        try:
            redis = await get_redis()
            key = _CACHE_KEY.format(session_id=str(session_id))
            data = await redis.get(key)
            if data:
                return SimSessionState.from_dict(json.loads(data))
        except Exception:
            pass
        return None

    async def _invalidate_cache(self, session_id: UUID) -> None:
        try:
            redis = await get_redis()
            await redis.delete(_CACHE_KEY.format(session_id=str(session_id)))
        except Exception:
            pass
