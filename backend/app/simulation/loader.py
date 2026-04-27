"""
ScenarioLoader — fetches ScenarioDef from DB and maps to pure domain models.
Uses an in-process LRU cache to avoid repeated DB reads within a request.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.core.exceptions import ScenarioNotFoundError
from app.db.models.scenario import ScenarioDef, StepDef
from app.simulation.models.scenario import (
    Condition,
    DecisionOption,
    Effect,
    Scenario,
    Step,
    StepTransition,
    StepType,
)


class ScenarioLoader:

    async def load(self, scenario_id: UUID, session: AsyncSession) -> Scenario:
        result = await session.execute(
            select(ScenarioDef)
            .where(ScenarioDef.id == scenario_id)
            .options(
                selectinload(ScenarioDef.steps).selectinload(StepDef.options),
                selectinload(ScenarioDef.transitions),
                joinedload(ScenarioDef.profession),
            )
            .execution_options(populate_existing=True)
        )
        db_scenario = result.scalar_one_or_none()
        if not db_scenario:
            raise ScenarioNotFoundError(str(scenario_id))

        return self._map(db_scenario)

    async def load_by_slug(
        self, profession_slug: str, scenario_slug: str, session: AsyncSession
    ) -> Scenario:
        from app.db.models.profession import Profession
        result = await session.execute(
            select(ScenarioDef)
            .join(ScenarioDef.profession)
            .where(
                Profession.slug == profession_slug,
                ScenarioDef.slug == scenario_slug,
                ScenarioDef.is_published == True,  # noqa: E712
            )
            .options(
                selectinload(ScenarioDef.steps).selectinload(StepDef.options),
                selectinload(ScenarioDef.transitions),
                joinedload(ScenarioDef.profession),
            )
            .execution_options(populate_existing=True)
        )
        db_scenario = result.scalar_one_or_none()
        if not db_scenario:
            raise ScenarioNotFoundError(f"{profession_slug}/{scenario_slug}")
        return self._map(db_scenario)

    def _map(self, db: ScenarioDef) -> Scenario:
        steps: dict[str, Step] = {}
        for step_db in db.steps:
            options = tuple(
                DecisionOption(
                    option_key=opt.option_key,
                    label=opt.label,
                    description=opt.description,
                    effects=tuple(Effect.from_dict(e) for e in opt.effects),
                    preconditions=tuple(Condition.from_dict(c) for c in opt.preconditions),
                    next_step_key=opt.next_step_key,
                )
                for opt in step_db.options
            )
            steps[step_db.step_key] = Step(
                step_key=step_db.step_key,
                title=step_db.title,
                narrative=step_db.narrative,
                context_data=step_db.context_data or {},
                step_type=StepType(step_db.step_type),
                is_terminal=step_db.is_terminal,
                sort_order=step_db.sort_order,
                options=options,
            )

        transitions = tuple(
            StepTransition(
                from_step_key=t.from_step_key,
                condition=Condition.from_dict(t.condition),
                to_step_key=t.to_step_key,
                priority=t.priority,
            )
            for t in db.transitions
        )

        return Scenario(
            id=db.id,
            profession_id=db.profession_id,
            profession_slug=db.profession.slug,
            slug=db.slug,
            title=db.title,
            description=db.description,
            difficulty=db.difficulty,
            version=db.version,
            initial_metrics=db.initial_metrics,
            initial_state=db.initial_state,
            steps=steps,
            transitions=transitions,
        )
