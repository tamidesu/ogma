from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.profession import Profession
from app.db.models.scenario import ScenarioDef


class ScenarioRepository:

    async def list_professions(self, db: AsyncSession) -> list[Profession]:
        result = await db.execute(
            select(Profession)
            .where(Profession.is_active == True)  # noqa: E712
            .order_by(Profession.name)
        )
        return list(result.scalars().all())

    async def get_profession_by_slug(self, slug: str, db: AsyncSession) -> Profession | None:
        result = await db.execute(
            select(Profession).where(Profession.slug == slug, Profession.is_active == True)  # noqa
        )
        return result.scalar_one_or_none()

    async def list_scenarios(
        self, profession_id: UUID, db: AsyncSession
    ) -> list[ScenarioDef]:
        result = await db.execute(
            select(ScenarioDef)
            .where(
                ScenarioDef.profession_id == profession_id,
                ScenarioDef.is_published == True,  # noqa
            )
            .order_by(ScenarioDef.difficulty, ScenarioDef.title)
        )
        return list(result.scalars().all())

    async def get_scenario(self, scenario_id: UUID, db: AsyncSession) -> ScenarioDef | None:
        result = await db.execute(
            select(ScenarioDef).where(ScenarioDef.id == scenario_id)
        )
        return result.scalar_one_or_none()
