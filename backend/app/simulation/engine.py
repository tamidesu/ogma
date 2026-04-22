"""
SimulationEngine — top-level entry point for the Service Layer.
Composes Loader + Executor. Has async DB access (for loading scenarios).
ZERO AI calls — AI is invoked above this layer by DecisionService.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.simulation.executor import StepExecutor
from app.simulation.loader import ScenarioLoader
from app.simulation.metrics import MetricsCalculator
from app.simulation.models.outcome import StepOutcome
from app.simulation.models.session_state import SimSessionState
from app.simulation.rule_evaluator import RuleEvaluator
from app.simulation.state_machine import StateTransitionEngine


def _build_executor() -> StepExecutor:
    rule_evaluator = RuleEvaluator()
    state_machine = StateTransitionEngine(rule_evaluator)
    metrics_calc = MetricsCalculator()
    return StepExecutor(rule_evaluator, state_machine, metrics_calc)


class SimulationEngine:
    """Singleton-friendly: stateless, all state passed as arguments."""

    def __init__(self):
        self._loader = ScenarioLoader()
        self._executor = _build_executor()
        self._metrics = MetricsCalculator()

    async def execute_step(
        self,
        session_state: SimSessionState,
        option_key: str,
        db: AsyncSession,
    ) -> StepOutcome:
        scenario = await self._loader.load(session_state.scenario_id, db)
        return self._executor.execute(scenario, session_state, option_key)

    async def build_initial_state(
        self,
        scenario_id,
        session_id,
        db: AsyncSession,
    ) -> SimSessionState:
        from app.simulation.models.session_state import MetricSnapshot
        scenario = await self._loader.load(scenario_id, db)
        first_step_key = next(
            s.step_key for s in sorted(scenario.steps.values(), key=lambda s: s.sort_order)
        )
        return SimSessionState(
            session_id=session_id,
            scenario_id=scenario_id,
            scenario_version=scenario.version,
            current_step_key=first_step_key,
            metrics=MetricSnapshot.from_dict(scenario.initial_metrics),
            state=dict(scenario.initial_state),
            unlocked_steps=set(),
            step_count=0,
        )

    def get_available_options(
        self,
        session_state: SimSessionState,
        scenario,
    ) -> list[dict]:
        """
        Returns options visible to the current user based on preconditions.
        Creative addition: unlocked_steps also gate option visibility.
        """
        rule_evaluator = RuleEvaluator()
        step = scenario.get_step(session_state.current_step_key)
        if not step:
            return []
        return [
            {
                "option_key": opt.option_key,
                "label": opt.label,
                "description": opt.description,
                "is_available": rule_evaluator.check_preconditions(opt.preconditions, session_state),
            }
            for opt in step.options
        ]

    def compute_final_score(self, session_state: SimSessionState, profession_slug: str) -> float:
        return self._metrics.compute_final_score(
            session_state.metrics.to_dict(), profession_slug
        )
