from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.skill_profile import CompletedScenario, SkillProfile, SkillScore


class SkillRepository:

    async def get_or_create_profile(
        self, user_id: UUID, db: AsyncSession
    ) -> SkillProfile:
        result = await db.execute(
            select(SkillProfile).where(SkillProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            profile = SkillProfile(user_id=user_id)
            db.add(profile)
            await db.flush()
            await db.refresh(profile)
        return profile

    async def get_profile_with_scores(
        self, user_id: UUID, db: AsyncSession
    ) -> SkillProfile | None:
        result = await db.execute(
            select(SkillProfile)
            .where(SkillProfile.user_id == user_id)
            .options(selectinload(SkillProfile.skill_scores))
        )
        return result.scalar_one_or_none()

    async def upsert_skill_score(
        self,
        profile_id: UUID,
        profession_id: UUID,
        skill_key: str,
        delta: float,
        db: AsyncSession,
    ) -> SkillScore:
        result = await db.execute(
            select(SkillScore).where(
                SkillScore.skill_profile_id == profile_id,
                SkillScore.profession_id == profession_id,
                SkillScore.skill_key == skill_key,
            )
        )
        skill = result.scalar_one_or_none()
        if skill:
            skill.score = round(min(999.99, float(skill.score) + delta), 2)
        else:
            skill = SkillScore(
                skill_profile_id=profile_id,
                profession_id=profession_id,
                skill_key=skill_key,
                score=round(max(0.0, delta), 2),
            )
            db.add(skill)
        await db.flush()
        return skill

    async def add_xp(
        self, profile: SkillProfile, xp: float, db: AsyncSession
    ) -> tuple[SkillProfile, bool]:
        """Returns (updated_profile, leveled_up)."""
        from app.simulation.metrics import MetricsCalculator
        calc = MetricsCalculator()

        old_level = profile.level
        profile.xp_total += int(xp)
        profile.level = calc.level_for_xp(profile.xp_total)
        leveled_up = profile.level > old_level
        await db.flush()
        return profile, leveled_up

    async def record_completed_scenario(
        self,
        user_id: UUID,
        scenario_id: UUID,
        session_id: UUID,
        profile_id: UUID,
        final_score: float,
        db: AsyncSession,
    ) -> CompletedScenario:
        record = CompletedScenario(
            user_id=user_id,
            scenario_id=scenario_id,
            session_id=session_id,
            skill_profile_id=profile_id,
            final_score=final_score,
            completed_at=datetime.now(timezone.utc),
        )
        db.add(record)
        await db.flush()
        return record

    async def list_completed(
        self, user_id: UUID, db: AsyncSession
    ) -> list[CompletedScenario]:
        result = await db.execute(
            select(CompletedScenario)
            .where(CompletedScenario.user_id == user_id)
            .order_by(CompletedScenario.completed_at.desc())
        )
        return list(result.scalars().all())
