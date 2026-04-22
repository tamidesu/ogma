"""
Pure Python domain models — no SQLAlchemy, no Pydantic, no I/O.
These are what the Simulation Engine operates on.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID


class StepType(str, Enum):
    DECISION = "decision"
    EXPOSITION = "exposition"
    TERMINAL = "terminal"


class EffectType(str, Enum):
    METRIC_DELTA = "metric_delta"
    METRIC_SET = "metric_set"
    STATE_SET = "state_set"
    STATE_TOGGLE = "state_toggle"
    SKILL_XP = "skill_xp"
    UNLOCK_STEP = "unlock_step"


class ConditionType(str, Enum):
    METRIC_GTE = "metric_gte"
    METRIC_LTE = "metric_lte"
    STATE_IS_TRUE = "state_is_true"
    STATE_EQUALS = "state_equals"
    NOT = "not"
    AND = "and"
    OR = "or"


@dataclass(frozen=True)
class Effect:
    type: EffectType
    # metric_delta / metric_set
    metric: str | None = None
    delta: float | None = None
    value: Any = None
    # state_set / state_toggle / unlock_step
    key: str | None = None
    # skill_xp
    skill: str | None = None
    xp: float | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "Effect":
        return cls(
            type=EffectType(d["type"]),
            metric=d.get("metric"),
            delta=d.get("delta"),
            value=d.get("value"),
            key=d.get("key"),
            skill=d.get("skill"),
            xp=d.get("xp"),
        )

    def to_dict(self) -> dict:
        return {k: v for k, v in {
            "type": self.type.value,
            "metric": self.metric,
            "delta": self.delta,
            "value": self.value,
            "key": self.key,
            "skill": self.skill,
            "xp": self.xp,
        }.items() if v is not None}


@dataclass(frozen=True)
class Condition:
    type: ConditionType
    metric: str | None = None
    value: Any = None
    key: str | None = None
    condition: "Condition | None" = None           # for NOT
    conditions: tuple["Condition", ...] = field(default_factory=tuple)  # for AND/OR

    @classmethod
    def from_dict(cls, d: dict) -> "Condition":
        ctype = ConditionType(d["type"])
        nested = None
        nested_list: tuple = ()

        if ctype == ConditionType.NOT:
            nested = cls.from_dict(d["condition"])
        elif ctype in (ConditionType.AND, ConditionType.OR):
            nested_list = tuple(cls.from_dict(c) for c in d.get("conditions", []))

        return cls(
            type=ctype,
            metric=d.get("metric"),
            value=d.get("value"),
            key=d.get("key"),
            condition=nested,
            conditions=nested_list,
        )


@dataclass(frozen=True)
class DecisionOption:
    option_key: str
    label: str
    description: str | None
    effects: tuple[Effect, ...]
    preconditions: tuple[Condition, ...]
    next_step_key: str | None

    @classmethod
    def from_dict(cls, d: dict) -> "DecisionOption":
        return cls(
            option_key=d["option_key"],
            label=d["label"],
            description=d.get("description"),
            effects=tuple(Effect.from_dict(e) for e in d.get("effects", [])),
            preconditions=tuple(Condition.from_dict(c) for c in d.get("preconditions", [])),
            next_step_key=d.get("next_step_key"),
        )


@dataclass(frozen=True)
class StepTransition:
    from_step_key: str
    condition: Condition
    to_step_key: str
    priority: int = 0

    @classmethod
    def from_dict(cls, d: dict) -> "StepTransition":
        return cls(
            from_step_key=d["from_step_key"],
            condition=Condition.from_dict(d["condition"]),
            to_step_key=d["to_step_key"],
            priority=d.get("priority", 0),
        )


@dataclass(frozen=True)
class Step:
    step_key: str
    title: str
    narrative: str
    context_data: dict[str, Any]
    step_type: StepType
    is_terminal: bool
    sort_order: int
    options: tuple[DecisionOption, ...]

    def get_option(self, option_key: str) -> DecisionOption | None:
        return next((o for o in self.options if o.option_key == option_key), None)


@dataclass(frozen=True)
class Scenario:
    id: UUID
    profession_id: UUID
    profession_slug: str
    slug: str
    title: str
    description: str
    difficulty: int
    version: int
    initial_metrics: dict[str, float]
    initial_state: dict[str, Any]
    steps: dict[str, Step]               # keyed by step_key
    transitions: tuple[StepTransition, ...]

    def get_step(self, step_key: str) -> Step | None:
        return self.steps.get(step_key)

    def get_transitions_from(self, step_key: str) -> list[StepTransition]:
        return sorted(
            [t for t in self.transitions if t.from_step_key == step_key],
            key=lambda t: t.priority,
            reverse=True,
        )
