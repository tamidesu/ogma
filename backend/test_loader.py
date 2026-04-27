import asyncio
import sys
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from app.db.session import async_session_factory
from app.db.models.scenario import ScenarioDef
from app.db.models.profession import Profession

async def main():
    scenario_id = UUID("9e9cf7cc-21c0-45af-bd47-4758efc2d170")
    async with async_session_factory() as session:
        result = await session.execute(
            select(ScenarioDef)
            .where(ScenarioDef.id == scenario_id)
            .options(
                joinedload(ScenarioDef.profession)
            )
        )
        scenario = result.scalar_one_or_none()
        print(f"Scenario: {scenario}")
        print(f"Profession ID: {scenario.profession_id}")
        print(f"Profession: {scenario.profession}")
        if scenario.profession is None:
            print("Trying to fetch profession directly")
            prof = await session.get(Profession, scenario.profession_id)
            print(f"Direct profession: {prof}")

if __name__ == "__main__":
    asyncio.run(main())
