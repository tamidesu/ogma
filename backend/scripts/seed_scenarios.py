"""
Seed script — loads all profession + scenario JSON fixtures into the database.
Idempotent: upserts by slug, safe to run multiple times.

Usage:
    python -m scripts.seed_scenarios
    python -m scripts.seed_scenarios --publish   # publish all scenarios
"""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import async_session_factory, init_db
from app.db.models.profession import Profession
from app.db.models.scenario import ScenarioDef, StepDef, OptionDef, StepTransition

FIXTURES_DIR = ROOT / "tests" / "fixtures" / "scenarios"


async def upsert_profession(data: dict, session: AsyncSession) -> Profession:
    result = await session.execute(
        select(Profession).where(Profession.slug == data["slug"])
    )
    profession = result.scalar_one_or_none()
    if profession:
        for k, v in data.items():
            setattr(profession, k, v)
    else:
        profession = Profession(**data)
        session.add(profession)
    await session.flush()
    await session.refresh(profession)
    return profession


async def upsert_scenario(
    data: dict, profession: Profession, publish: bool, session: AsyncSession
) -> ScenarioDef:
    result = await session.execute(
        select(ScenarioDef).where(
            ScenarioDef.profession_id == profession.id,
            ScenarioDef.slug == data["slug"],
        )
    )
    scenario_db = result.scalar_one_or_none()

    scenario_fields = {k: v for k, v in data.items() if k not in ("steps", "transitions", "profession")}
    scenario_fields["profession_id"] = profession.id
    if publish:
        scenario_fields["is_published"] = True

    if scenario_db:
        for k, v in scenario_fields.items():
            setattr(scenario_db, k, v)
        # Delete existing steps to re-seed cleanly
        from sqlalchemy import delete
        await session.execute(delete(StepDef).where(StepDef.scenario_id == scenario_db.id))
        await session.execute(delete(StepTransition).where(StepTransition.scenario_id == scenario_db.id))
    else:
        scenario_db = ScenarioDef(**scenario_fields)
        session.add(scenario_db)
    await session.flush()
    await session.refresh(scenario_db)

    # Seed steps + options
    for step_data in data.get("steps", []):
        options_data = step_data.pop("decision_options", [])
        step = StepDef(scenario_id=scenario_db.id, **step_data)
        session.add(step)
        await session.flush()
        await session.refresh(step)

        for opt_data in options_data:
            opt = OptionDef(step_id=step.id, **opt_data)
            session.add(opt)

    # Seed transitions
    for trans_data in data.get("transitions", []):
        trans = StepTransition(scenario_id=scenario_db.id, **trans_data)
        session.add(trans)

    await session.flush()
    return scenario_db


async def seed_file(path: Path, publish: bool, session: AsyncSession) -> None:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    profession_data = data["profession"]
    profession = await upsert_profession(profession_data, session)
    print(f"  ✓ Profession: {profession.slug}")

    for scenario_data in data.get("scenarios", []):
        scenario = await upsert_scenario(scenario_data, profession, publish, session)
        status = "published" if scenario.is_published else "draft"
        print(f"    ✓ Scenario [{status}]: {scenario.slug} ({len(scenario.steps)} steps)")


async def main(publish: bool = False) -> None:
    print("Initialising database connection...")
    await init_db()

    fixture_files = sorted(FIXTURES_DIR.glob("*.json"))
    if not fixture_files:
        print(f"No fixture files found in {FIXTURES_DIR}")
        return

    async with async_session_factory() as session:
        for path in fixture_files:
            print(f"\nSeeding: {path.name}")
            await seed_file(path, publish, session)
        await session.commit()

    print(f"\n✅ Seeded {len(fixture_files)} profession files.")
    if not publish:
        print("   Tip: run with --publish to make scenarios available to users.")


if __name__ == "__main__":
    publish_flag = "--publish" in sys.argv
    asyncio.run(main(publish=publish_flag))
