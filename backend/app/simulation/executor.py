"""
StepExecutor — runs one decision step end-to-end.
Pure computation: takes domain objects, returns StepOutcome.
No DB, no AI, no async.
"""
import copy

from app.core.exceptions import InvalidDecisionError, PreconditionNotMetError
from app.simulation.metrics import MetricsCalculator
from app.simulation.models.outcome import StepOutcome
from app.simulation.models.scenario import Scenario
from app.simulation.models.session_state import MetricSnapshot, SimSessionState
from app.simulation.rule_evaluator import RuleEvaluator
from app.simulation.state_machine import StateTransitionEngine


class StepExecutor:

    def __init__(
        self,
        rule_evaluator: RuleEvaluator,
        state_machine: StateTransitionEngine,
        metrics_calc: MetricsCalculator,
    ):
        self._rules = rule_evaluator
        self._state_machine = state_machine
        self._metrics = metrics_calc

    def execute(
        self,
        scenario: Scenario,
        state: SimSessionState,
        option_key: str,
    ) -> StepOutcome:
        step = scenario.get_step(state.current_step_key)
        if not step:
            raise InvalidDecisionError(option_key)

        option = step.get_option(option_key)
        if not option:
            raise InvalidDecisionError(option_key)

        # Snapshot state before mutation
        metrics_before = MetricSnapshot(dict(state.metrics.values))
        state_before = copy.deepcopy(state.state)

        # Check preconditions
        if not self._rules.check_preconditions(option.preconditions, state):
            raise PreconditionNotMetError(option_key)

        # Apply effects — state is mutated in-place
        deltas, xp_gains = self._rules.apply_effects(option.effects, state)

        # Post-effect snapshots
        metrics_after = MetricSnapshot(dict(state.metrics.values))
        state_after = copy.deepcopy(state.state)

        # Score for this step
        step_score = self._metrics.compute_step_score(
            metrics_before.to_dict(),
            metrics_after.to_dict(),
            scenario.profession_slug,
        )

        # Add step score to running score metric
        current_score = state.metrics.get("score", 0.0)
        state.metrics = state.metrics.with_update("score", round(current_score + step_score, 2))

        # Determine next step
        next_step_key = self._state_machine.resolve_next_step(scenario, state, option.next_step_key)

        # Determine terminal status
        is_terminal = (
            next_step_key is None
            or (next_step_key and scenario.get_step(next_step_key) is not None
                and scenario.get_step(next_step_key).is_terminal)
        )

        # Advance session state
        if next_step_key:
            state.current_step_key = next_step_key
        state.step_count += 1

        return StepOutcome(
            step=step,
            option=option,
            deltas=deltas,
            metrics_before=metrics_before,
            metrics_after=metrics_after,
            state_before=state_before,
            state_after=state_after,
            next_step_key=next_step_key,
            is_terminal=is_terminal,
            skill_xp_gains=xp_gains,
            step_score=step_score,
        )
