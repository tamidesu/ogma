from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.skill_repo import SkillRepository
from app.simulation.models.outcome import SkillXPGain

logger = structlog.get_logger(__name__)
skill_repo = SkillRepository()


class ProgressService:

    async def apply_skill_effects(
        self,
        user_id: UUID,
        profession_id: UUID,
        xp_gains: tuple[SkillXPGain, ...],
        db: AsyncSession,
    ) -> tuple[int, bool]:
        """
        Apply XP gains from a decision step.
        Returns (total_xp_gained, leveled_up).
        """
        if not xp_gains:
            return 0, False

        profile = await skill_repo.get_or_create_profile(user_id, db)
        total_xp = 0

        for gain in xp_gains:
            await skill_repo.upsert_skill_score(
                profile.id, profession_id, gain.skill, gain.xp, db
            )
            total_xp += int(gain.xp)

        profile, leveled_up = await skill_repo.add_xp(profile, total_xp, db)

        if leveled_up:
            logger.info(
                "level_up",
                user_id=str(user_id),
                new_level=profile.level,
                total_xp=profile.xp_total,
            )

        return total_xp, leveled_up

    async def record_completion(
        self,
        user_id: UUID,
        scenario_id: UUID,
        session_id: UUID,
        final_score: float,
        db: AsyncSession,
    ) -> None:
        profile = await skill_repo.get_or_create_profile(user_id, db)
        await skill_repo.record_completed_scenario(
            user_id, scenario_id, session_id, profile.id, final_score, db
        )

    async def get_progress_summary(self, user_id: UUID, db: AsyncSession) -> dict:
        profile = await skill_repo.get_profile_with_scores(user_id, db)
        if not profile:
            return {"level": 1, "xp_total": 0, "skill_scores": [], "completed_scenarios": []}

        completed = await skill_repo.list_completed(user_id, db)

        from app.simulation.metrics import MetricsCalculator
        calc = MetricsCalculator()

        return {
            "level": profile.level,
            "xp_total": profile.xp_total,
            "xp_to_next_level": calc.xp_to_next_level(profile.xp_total, profile.level),
            "skill_scores": [
                {
                    "profession_id": str(s.profession_id),
                    "skill_key": s.skill_key,
                    "score": float(s.score),
                }
                for s in (profile.skill_scores or [])
            ],
            "scenarios_completed": len(completed),
        }
