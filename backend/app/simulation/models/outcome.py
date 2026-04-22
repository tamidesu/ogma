from dataclasses import dataclass, field
from typing import Any

from app.simulation.models.scenario import DecisionOption, Effect, Step
from app.simulation.models.session_state import MetricSnapshot


@dataclass(frozen=True)
class SkillXPGain:
    skill: str
    xp: float


@dataclass(frozen=True)
class StateDelta:
    """Describes a single atomic change applied to session state."""
    effect: Effect
    # Resolved values after application
    metric_key: str | None = None
    old_value: Any = None
    new_value: Any = None


@dataclass(frozen=True)
class StepOutcome:
    """
    The complete result of executing one decision step.
    Returned by SimulationEngine — contains everything needed
    to build the API response without querying the DB again.
    """
    step: Step
    option: DecisionOption
    deltas: tuple[StateDelta, ...]

    metrics_before: MetricSnapshot
    metrics_after: MetricSnapshot
    state_before: dict[str, Any]
    state_after: dict[str, Any]

    next_step_key: str | None
    is_terminal: bool

    skill_xp_gains: tuple[SkillXPGain, ...]

    # Score delta from this step (computed by MetricsCalculator)
    step_score: float = 0.0

    @property
    def effects_applied(self) -> list[dict]:
        return [d.effect.to_dict() for d in self.deltas]
