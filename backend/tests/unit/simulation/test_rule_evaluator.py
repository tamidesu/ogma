"""Unit tests for RuleEvaluator — no DB, no AI, no async."""
import pytest
from uuid import uuid4

from app.simulation.models.scenario import Condition, ConditionType, Effect, EffectType
from app.simulation.models.session_state import MetricSnapshot, SimSessionState
from app.simulation.rule_evaluator import RuleEvaluator


def make_state(metrics: dict = None, state: dict = None) -> SimSessionState:
    return SimSessionState(
        session_id=uuid4(),
        scenario_id=uuid4(),
        scenario_version=1,
        current_step_key="step_1",
        metrics=MetricSnapshot.from_dict(metrics or {"risk": 50, "reputation": 50}),
        state=state or {},
        unlocked_steps=set(),
    )


@pytest.fixture
def evaluator():
    return RuleEvaluator()


# ── Conditions ────────────────────────────────────────────

class TestConditions:
    def test_metric_gte_true(self, evaluator):
        state = make_state({"reputation": 60})
        cond = Condition(type=ConditionType.METRIC_GTE, metric="reputation", value=55)
        assert evaluator._eval_condition(cond, state) is True

    def test_metric_gte_false(self, evaluator):
        state = make_state({"reputation": 40})
        cond = Condition(type=ConditionType.METRIC_GTE, metric="reputation", value=55)
        assert evaluator._eval_condition(cond, state) is False

    def test_metric_lte(self, evaluator):
        state = make_state({"risk": 20})
        cond = Condition(type=ConditionType.METRIC_LTE, metric="risk", value=30)
        assert evaluator._eval_condition(cond, state) is True

    def test_state_is_true(self, evaluator):
        state = make_state(state={"incident_active": True})
        cond = Condition(type=ConditionType.STATE_IS_TRUE, key="incident_active")
        assert evaluator._eval_condition(cond, state) is True

    def test_state_is_true_missing_key(self, evaluator):
        state = make_state()
        cond = Condition(type=ConditionType.STATE_IS_TRUE, key="nonexistent")
        assert evaluator._eval_condition(cond, state) is False

    def test_state_equals(self, evaluator):
        state = make_state(state={"status": "active"})
        cond = Condition(type=ConditionType.STATE_EQUALS, key="status", value="active")
        assert evaluator._eval_condition(cond, state) is True

    def test_not_condition(self, evaluator):
        state = make_state({"risk": 80})
        inner = Condition(type=ConditionType.METRIC_LTE, metric="risk", value=50)
        cond = Condition(type=ConditionType.NOT, condition=inner)
        assert evaluator._eval_condition(cond, state) is True

    def test_and_all_true(self, evaluator):
        state = make_state({"risk": 20, "reputation": 70})
        cond = Condition(
            type=ConditionType.AND,
            conditions=(
                Condition(type=ConditionType.METRIC_LTE, metric="risk", value=30),
                Condition(type=ConditionType.METRIC_GTE, metric="reputation", value=60),
            ),
        )
        assert evaluator._eval_condition(cond, state) is True

    def test_and_one_false(self, evaluator):
        state = make_state({"risk": 20, "reputation": 40})
        cond = Condition(
            type=ConditionType.AND,
            conditions=(
                Condition(type=ConditionType.METRIC_LTE, metric="risk", value=30),
                Condition(type=ConditionType.METRIC_GTE, metric="reputation", value=60),
            ),
        )
        assert evaluator._eval_condition(cond, state) is False

    def test_or_one_true(self, evaluator):
        state = make_state({"risk": 20, "reputation": 40})
        cond = Condition(
            type=ConditionType.OR,
            conditions=(
                Condition(type=ConditionType.METRIC_LTE, metric="risk", value=30),
                Condition(type=ConditionType.METRIC_GTE, metric="reputation", value=60),
            ),
        )
        assert evaluator._eval_condition(cond, state) is True


# ── Effects ───────────────────────────────────────────────

class TestEffects:
    def test_metric_delta_increases(self, evaluator):
        state = make_state({"reputation": 50})
        effects = (Effect(type=EffectType.METRIC_DELTA, metric="reputation", delta=10),)
        evaluator.apply_effects(effects, state)
        assert state.metrics.get("reputation") == 60.0

    def test_metric_delta_clamped_at_100(self, evaluator):
        state = make_state({"reputation": 95})
        effects = (Effect(type=EffectType.METRIC_DELTA, metric="reputation", delta=20),)
        evaluator.apply_effects(effects, state)
        assert state.metrics.get("reputation") == 100.0

    def test_metric_delta_clamped_at_zero(self, evaluator):
        state = make_state({"risk": 5})
        effects = (Effect(type=EffectType.METRIC_DELTA, metric="risk", delta=-20),)
        evaluator.apply_effects(effects, state)
        assert state.metrics.get("risk") == 0.0

    def test_metric_set(self, evaluator):
        state = make_state({"reputation": 50})
        effects = (Effect(type=EffectType.METRIC_SET, metric="reputation", value=75),)
        evaluator.apply_effects(effects, state)
        assert state.metrics.get("reputation") == 75.0

    def test_state_set(self, evaluator):
        state = make_state()
        effects = (Effect(type=EffectType.STATE_SET, key="incident_resolved", value=True),)
        evaluator.apply_effects(effects, state)
        assert state.get_state("incident_resolved") is True

    def test_state_toggle(self, evaluator):
        state = make_state(state={"flag": True})
        effects = (Effect(type=EffectType.STATE_TOGGLE, key="flag"),)
        evaluator.apply_effects(effects, state)
        assert state.get_state("flag") is False

    def test_skill_xp_returned(self, evaluator):
        state = make_state()
        effects = (Effect(type=EffectType.SKILL_XP, skill="debugging", xp=30),)
        _, xp_gains = evaluator.apply_effects(effects, state)
        assert len(xp_gains) == 1
        assert xp_gains[0].skill == "debugging"
        assert xp_gains[0].xp == 30

    def test_unlock_step(self, evaluator):
        state = make_state()
        effects = (Effect(type=EffectType.UNLOCK_STEP, key="secret_path"),)
        evaluator.apply_effects(effects, state)
        assert "secret_path" in state.unlocked_steps

    def test_multiple_effects_applied_in_order(self, evaluator):
        state = make_state({"risk": 50, "reputation": 50})
        effects = (
            Effect(type=EffectType.METRIC_DELTA, metric="risk", delta=-10),
            Effect(type=EffectType.METRIC_DELTA, metric="reputation", delta=15),
        )
        evaluator.apply_effects(effects, state)
        assert state.metrics.get("risk") == 40.0
        assert state.metrics.get("reputation") == 65.0
