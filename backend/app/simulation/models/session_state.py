from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class MetricSnapshot:
    """Immutable point-in-time metric values."""
    values: dict[str, float]

    def get(self, key: str, default: float = 0.0) -> float:
        return self.values.get(key, default)

    def with_update(self, key: str, new_value: float) -> "MetricSnapshot":
        return MetricSnapshot({**self.values, key: new_value})

    def to_dict(self) -> dict[str, float]:
        return dict(self.values)

    @classmethod
    def from_dict(cls, d: dict) -> "MetricSnapshot":
        return cls(values={k: float(v) for k, v in d.items()})


@dataclass
class SimSessionState:
    """
    Full mutable simulation state for one session.
    Serialised to/from JSONB via to_dict/from_dict.
    The engine always works with this typed model — never raw dicts.
    """
    session_id: UUID
    scenario_id: UUID
    scenario_version: int
    current_step_key: str
    metrics: MetricSnapshot
    state: dict[str, Any]              # boolean/string flags (domain state)
    unlocked_steps: set[str]           # steps made available by unlock_step effects
    step_count: int = 0                # total decisions made

    def get_state(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        self.state[key] = value

    def toggle_state(self, key: str) -> None:
        self.state[key] = not bool(self.state.get(key, False))

    def unlock_step(self, step_key: str) -> None:
        self.unlocked_steps.add(step_key)

    def to_dict(self) -> dict:
        return {
            "session_id": str(self.session_id),
            "scenario_id": str(self.scenario_id),
            "scenario_version": self.scenario_version,
            "current_step_key": self.current_step_key,
            "metrics": self.metrics.to_dict(),
            "state": self.state,
            "unlocked_steps": list(self.unlocked_steps),
            "step_count": self.step_count,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SimSessionState":
        return cls(
            session_id=UUID(d["session_id"]),
            scenario_id=UUID(d["scenario_id"]),
            scenario_version=d.get("scenario_version", 1),
            current_step_key=d["current_step_key"],
            metrics=MetricSnapshot.from_dict(d.get("metrics", {})),
            state=d.get("state", {}),
            unlocked_steps=set(d.get("unlocked_steps", [])),
            step_count=d.get("step_count", 0),
        )
