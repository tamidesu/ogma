"""
StateTransitionEngine — determines the next step after a decision.
Pure logic: no DB, no AI.
"""
from app.simulation.models.scenario import Scenario
from app.simulation.models.session_state import SimSessionState
from app.simulation.rule_evaluator import RuleEvaluator


class StateTransitionEngine:

    def __init__(self, rule_evaluator: RuleEvaluator):
        self._rules = rule_evaluator

    def resolve_next_step(
        self,
        scenario: Scenario,
        state: SimSessionState,
        option_next_step_key: str | None,
    ) -> str | None:
        """
        Priority:
        1. Explicit transition rules (sorted by priority desc) that match state
        2. option.next_step_key
        3. None → scenario is terminal
        """
        transitions = scenario.get_transitions_from(state.current_step_key)
        for transition in transitions:
            if self._rules.check_preconditions((transition.condition,), state):
                return transition.to_step_key

        return option_next_step_key
