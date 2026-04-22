"""Unit tests for StepExecutor — full engine pipeline, no DB/AI."""
import pytest
from uuid import uuid4

from app.core.exceptions import InvalidDecisionError, PreconditionNotMetError
from app.simulation.executor import StepExecutor
from app.simulation.metrics import MetricsCalculator
from app.simulation.models.scenario import (
    Condition, ConditionType, DecisionOption, Effect, EffectType,
    Scenario, Step, StepType,
)
from app.simulation.models.session_state import MetricSnapshot, SimSessionState
from app.simulation.rule_evaluator import RuleEvaluator
from app.simulation.state_machine import StateTransitionEngine


def build_executor() -> StepExecutor:
    rules = RuleEvaluator()
    return StepExecutor(rules, StateTransitionEngine(rules), MetricsCalculator())


def make_scenario(steps: list[Step], transitions=()) -> Scenario:
    return Scenario(
        id=uuid4(),
        profession_id=uuid4(),
        profession_slug="software_engineer",
        slug="test_scenario",
        title="Test",
        description="Test scenario",
        difficulty=1,
        version=1,
        initial_metrics={"risk": 50, "reputation": 50, "score": 0},
        initial_state={},
        steps={s.step_key: s for s in steps},
        transitions=tuple(transitions),
    )


def make_state(metrics: dict, state: dict = None, step_key: str = "step_1") -> SimSessionState:
    return SimSessionState(
        session_id=uuid4(),
        scenario_id=uuid4(),
        scenario_version=1,
        current_step_key=step_key,
        metrics=MetricSnapshot.from_dict(metrics),
        state=state or {},
        unlocked_steps=set(),
    )


def make_step(
    step_key: str = "step_1",
    options: list[DecisionOption] = None,
    is_terminal: bool = False,
    next_step_key: str = "step_2",
) -> Step:
    if options is None:
        options = [
            DecisionOption(
                option_key="option_a",
                label="Option A",
                description=None,
                effects=(Effect(type=EffectType.METRIC_DELTA, metric="reputation", delta=10),),
                preconditions=(),
                next_step_key=next_step_key,
            )
        ]
    return Step(
        step_key=step_key,
        title="Test Step",
        narrative="Test narrative",
        context_data={},
        step_type=StepType.TERMINAL if is_terminal else StepType.DECISION,
        is_terminal=is_terminal,
        sort_order=1,
        options=tuple(options),
    )


class TestStepExecutor:
    def test_basic_execution(self):
        executor = build_executor()
        step_2 = make_step("step_2", options=[], is_terminal=True, next_step_key=None)
        step_1 = make_step("step_1", next_step_key="step_2")
        scenario = make_scenario([step_1, step_2])
        state = make_state({"reputation": 50, "score": 0})

        outcome = executor.execute(scenario, state, "option_a")

        assert outcome.option.option_key == "option_a"
        assert outcome.metrics_after.get("reputation") == 60.0
        assert state.current_step_key == "step_2"
        assert state.step_count == 1

    def test_invalid_option_key_raises(self):
        executor = build_executor()
        scenario = make_scenario([make_step()])
        state = make_state({"reputation": 50, "score": 0})

        with pytest.raises(InvalidDecisionError):
            executor.execute(scenario, state, "nonexistent_option")

    def test_precondition_not_met_raises(self):
        executor = build_executor()
        guarded_option = DecisionOption(
            option_key="guarded",
            label="Guarded",
            description=None,
            effects=(),
            preconditions=(
                Condition(type=ConditionType.METRIC_GTE, metric="reputation", value=80),
            ),
            next_step_key=None,
        )
        step = make_step(options=[guarded_option])
        scenario = make_scenario([step])
        state = make_state({"reputation": 40, "score": 0})

        with pytest.raises(PreconditionNotMetError):
            executor.execute(scenario, state, "guarded")

    def test_precondition_met_executes(self):
        executor = build_executor()
        guarded_option = DecisionOption(
            option_key="guarded",
            label="Guarded",
            description=None,
            effects=(Effect(type=EffectType.METRIC_DELTA, metric="reputation", delta=5),),
            preconditions=(
                Condition(type=ConditionType.METRIC_GTE, metric="reputation", value=60),
            ),
            next_step_key=None,
        )
        step = make_step(options=[guarded_option])
        scenario = make_scenario([step])
        state = make_state({"reputation": 70, "score": 0})

        outcome = executor.execute(scenario, state, "guarded")
        assert outcome.metrics_after.get("reputation") == 75.0

    def test_terminal_step_sets_is_terminal(self):
        executor = build_executor()
        terminal_option = DecisionOption(
            option_key="finish",
            label="Finish",
            description=None,
            effects=(),
            preconditions=(),
            next_step_key=None,
        )
        step = make_step(options=[terminal_option], next_step_key=None)
        terminal = make_step("terminal_step", options=[], is_terminal=True, next_step_key=None)
        option_with_terminal = DecisionOption(
            option_key="go_terminal",
            label="Go to terminal",
            description=None,
            effects=(),
            preconditions=(),
            next_step_key="terminal_step",
        )
        step_1 = make_step(options=[option_with_terminal])
        scenario = make_scenario([step_1, terminal])
        state = make_state({"score": 0})

        outcome = executor.execute(scenario, state, "go_terminal")
        assert outcome.is_terminal is True

    def test_skill_xp_gains_captured(self):
        executor = build_executor()
        option = DecisionOption(
            option_key="learn",
            label="Learn",
            description=None,
            effects=(
                Effect(type=EffectType.SKILL_XP, skill="debugging", xp=25),
                Effect(type=EffectType.SKILL_XP, skill="leadership", xp=15),
            ),
            preconditions=(),
            next_step_key=None,
        )
        step = make_step(options=[option])
        scenario = make_scenario([step])
        state = make_state({"score": 0})

        outcome = executor.execute(scenario, state, "learn")
        skills = {g.skill: g.xp for g in outcome.skill_xp_gains}
        assert skills["debugging"] == 25
        assert skills["leadership"] == 15
