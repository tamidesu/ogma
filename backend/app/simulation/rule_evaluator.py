"""
RuleEvaluator — 100% pure, deterministic, no I/O.
Evaluates condition trees and applies effect lists to session state.
"""
from typing import Any

from app.core.exceptions import PreconditionNotMetError
from app.simulation.models.scenario import (
    Condition,
    ConditionType,
    Effect,
    EffectType,
)
from app.simulation.models.session_state import MetricSnapshot, SimSessionState
from app.simulation.models.outcome import SkillXPGain, StateDelta


class RuleEvaluator:

    # ── Condition evaluation ──────────────────────────────

    def check_preconditions(
        self,
        conditions: tuple[Condition, ...],
        state: SimSessionState,
    ) -> bool:
        """All top-level preconditions must pass (implicit AND)."""
        return all(self._eval_condition(c, state) for c in conditions)

    def _eval_condition(self, cond: Condition, state: SimSessionState) -> bool:
        match cond.type:
            case ConditionType.METRIC_GTE:
                return state.metrics.get(cond.metric) >= cond.value
            case ConditionType.METRIC_LTE:
                return state.metrics.get(cond.metric) <= cond.value
            case ConditionType.STATE_IS_TRUE:
                return bool(state.get_state(cond.key))
            case ConditionType.STATE_EQUALS:
                return state.get_state(cond.key) == cond.value
            case ConditionType.NOT:
                return not self._eval_condition(cond.condition, state)
            case ConditionType.AND:
                return all(self._eval_condition(c, state) for c in cond.conditions)
            case ConditionType.OR:
                return any(self._eval_condition(c, state) for c in cond.conditions)
            case _:
                return False

    # ── Effect application ────────────────────────────────

    def apply_effects(
        self,
        effects: tuple[Effect, ...],
        state: SimSessionState,
    ) -> tuple[tuple[StateDelta, ...], tuple[SkillXPGain, ...]]:
        """
        Apply all effects to state in-place.
        Returns (deltas_for_log, skill_xp_gains).
        State is mutated directly — caller holds the lock.
        """
        deltas: list[StateDelta] = []
        xp_gains: list[SkillXPGain] = []

        for effect in effects:
            delta = self._apply_effect(effect, state)
            if delta:
                deltas.append(delta)
            if effect.type == EffectType.SKILL_XP and effect.skill and effect.xp:
                xp_gains.append(SkillXPGain(skill=effect.skill, xp=effect.xp))

        return tuple(deltas), tuple(xp_gains)

    def _apply_effect(self, effect: Effect, state: SimSessionState) -> StateDelta | None:
        match effect.type:
            case EffectType.METRIC_DELTA:
                old = state.metrics.get(effect.metric)
                new = round(max(0.0, min(100.0, old + effect.delta)), 2)
                state.metrics = state.metrics.with_update(effect.metric, new)
                return StateDelta(effect=effect, metric_key=effect.metric, old_value=old, new_value=new)

            case EffectType.METRIC_SET:
                old = state.metrics.get(effect.metric)
                new = round(max(0.0, min(100.0, float(effect.value))), 2)
                state.metrics = state.metrics.with_update(effect.metric, new)
                return StateDelta(effect=effect, metric_key=effect.metric, old_value=old, new_value=new)

            case EffectType.STATE_SET:
                old = state.get_state(effect.key)
                state.set_state(effect.key, effect.value)
                return StateDelta(effect=effect, old_value=old, new_value=effect.value)

            case EffectType.STATE_TOGGLE:
                old = state.get_state(effect.key)
                state.toggle_state(effect.key)
                return StateDelta(effect=effect, old_value=old, new_value=not bool(old))

            case EffectType.SKILL_XP:
                # Recorded as XPGain, not a state delta
                return None

            case EffectType.UNLOCK_STEP:
                state.unlock_step(effect.key)
                return StateDelta(effect=effect, old_value=None, new_value=effect.key)

            case _:
                return None
