from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SessionStartedEvent(DomainEvent):
    session_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    scenario_id: UUID = field(default_factory=uuid4)


@dataclass
class DecisionMadeEvent(DomainEvent):
    session_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    step_key: str = ""
    option_key: str = ""
    metrics_after: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionCompletedEvent(DomainEvent):
    session_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    final_score: float = 0.0


@dataclass
class LevelUpEvent(DomainEvent):
    user_id: UUID = field(default_factory=uuid4)
    new_level: int = 1
    total_xp: int = 0
