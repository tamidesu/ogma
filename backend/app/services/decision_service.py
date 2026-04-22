from datetime import datetime, timezone
from uuid import UUID

import structlog
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.feedback_generator import FeedbackGenerator
from app.config import settings
from app.core.exceptions import SessionNotActiveError
from app.db.repositories.scenario_repo import ScenarioRepository
from app.db.repositories.session_repo import SessionRepository
from app.db.repositories.skill_repo import SkillRepository
from app.db.session import async_session_factory
from app.services.progress_service import ProgressService
from app.services.session_service import SessionService
from app.simulation.engine import SimulationEngine
from app.simulation.models.outcome import StepOutcome

logger = structlog.get_logger(__name__)

session_service = SessionService()
progress_service = ProgressService()
scenario_repo = ScenarioRepository()
session_repo = SessionRepository()
engine = SimulationEngine()
feedback_generator = FeedbackGenerator()


class DecisionService:

    async def process(
        self,
        session_id: UUID,
        option_key: str,
        user_id: UUID,
        db: AsyncSession,
        background_tasks: BackgroundTasks,
        time_spent_sec: int | None = None,
    ) -> dict:
        """
        Main decision processing pipeline:
        1. Load session + validate
        2. Run simulation engine (deterministic, no AI)
        3. Persist state + decision log
        4. Apply skill XP
        5. Dispatch AI feedback as BackgroundTask
        6. Return full response DTO
        """
        # ── 1. Load session ──────────────────────────────
        sim_session, state = await session_service.load_session(session_id, user_id, db)

        if sim_session.status != "active":
            raise SessionNotActiveError(sim_session.status)

        # Load scenario to get profession_slug for scoring
        scenario_db = await scenario_repo.get_scenario(sim_session.scenario_id, db)

        # ── 2. Execute step (pure computation) ───────────
        outcome: StepOutcome = await engine.execute_step(state, option_key, db)

        # ── 3. Persist state ─────────────────────────────
        decided_at = datetime.now(timezone.utc)

        if outcome.is_terminal:
            final_score = engine.compute_final_score(state, scenario_db.profession.slug if scenario_db else "")
            await session_service.complete_session(sim_session, final_score, db)
        else:
            await session_service.persist_state(sim_session, state, db)

        decision_log = await session_repo.log_decision(
            session_id=session_id,
            step_key=outcome.step.step_key,
            option_key=option_key,
            effects_applied=outcome.effects_applied,
            metrics_before=outcome.metrics_before.to_dict(),
            metrics_after=outcome.metrics_after.to_dict(),
            state_before=outcome.state_before,
            state_after=outcome.state_after,
            decided_at=decided_at,
            time_spent_sec=time_spent_sec,
            db=db,
        )

        # ── 4. Apply skill XP ────────────────────────────
        total_xp, leveled_up = 0, False
        if outcome.skill_xp_gains and scenario_db:
            total_xp, leveled_up = await progress_service.apply_skill_effects(
                user_id=user_id,
                profession_id=scenario_db.profession_id,
                xp_gains=outcome.skill_xp_gains,
                db=db,
            )
        if outcome.is_terminal and scenario_db:
            await progress_service.record_completion(
                user_id, sim_session.scenario_id, session_id,
                float(sim_session.final_score or 0), db
            )

        # ── 5. Dispatch AI feedback (async, non-blocking) ─
        profession_slug = scenario_db.profession.slug if scenario_db else "unknown"
        if settings.ai_feedback_async:
            # Fetch recent history now (while DB session is open) to enrich AI context
            recent_logs = await session_repo.get_history(
                session_id, db, limit=settings.ai_feedback_history_depth
            )
            db_history = [
                {
                    "step_key": log.step_key,
                    "step_title": getattr(log, "step_title", log.step_key),
                    "option_key": log.option_key,
                    "option_label": getattr(log, "option_label", log.option_key),
                    "metrics_before": log.metrics_before or {},
                    "metrics_after": log.metrics_after or {},
                }
                for log in recent_logs
            ]
            background_tasks.add_task(
                self._generate_and_attach_feedback,
                outcome=outcome,
                state_snapshot=state.to_dict(),
                profession_slug=profession_slug,
                session_id=session_id,
                log_id=decision_log.id,
                db_history=db_history,
            )

        # ── 6. Build response ─────────────────────────────
        next_step_info = None
        if outcome.next_step_key and not outcome.is_terminal:
            scenario = await engine._loader.load(sim_session.scenario_id, db)
            next_step = scenario.get_step(outcome.next_step_key)
            if next_step:
                available_options = engine.get_available_options(state, scenario)
                next_step_info = {
                    "step_key": next_step.step_key,
                    "title": next_step.title,
                    "narrative": next_step.narrative,
                    "step_type": next_step.step_type.value,
                    "available_options": available_options,
                }

        return {
            "decision_id": str(decision_log.id),
            "option_key": option_key,
            "effects_applied": outcome.effects_applied,
            "metrics_before": outcome.metrics_before.to_dict(),
            "metrics_after": outcome.metrics_after.to_dict(),
            "step_score": outcome.step_score,
            "next_step": next_step_info,
            "is_terminal": outcome.is_terminal,
            "final_score": float(sim_session.final_score) if outcome.is_terminal else None,
            "skills_earned": [
                {"skill": g.skill, "xp_gained": g.xp}
                for g in outcome.skill_xp_gains
            ],
            "xp_gained": total_xp,
            "leveled_up": leveled_up,
            "ai_feedback": {"text": None, "generated": False},  # Filled via SSE/polling
        }

    async def _generate_and_attach_feedback(
        self,
        outcome: StepOutcome,
        state_snapshot: dict,
        profession_slug: str,
        session_id: UUID,
        log_id: UUID,
        db_history: list[dict] | None = None,
    ) -> None:
        """Runs in background — uses its own DB session."""
        from app.simulation.models.session_state import SimSessionState

        async with async_session_factory() as bg_db:
            state = SimSessionState.from_dict(state_snapshot)
            feedback = await feedback_generator.generate(
                outcome=outcome,
                state=state,
                profession_slug=profession_slug,
                session_id=session_id,
                db=bg_db,
                db_history=db_history,
            )
            if feedback:
                await session_repo.attach_feedback(log_id, feedback.id, bg_db)
                await bg_db.commit()
