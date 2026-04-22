import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKey


class DecisionLog(Base, UUIDPrimaryKey):
    __tablename__ = "decision_log"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("simulation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_key: Mapped[str] = mapped_column(String(100), nullable=False)
    option_key: Mapped[str] = mapped_column(String(100), nullable=False)
    effects_applied: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    metrics_before: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    metrics_after: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    state_before: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    state_after: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Nullable FK — set asynchronously when AI feedback arrives
    ai_feedback_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_feedback.id"), nullable=True
    )
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_spent_sec: Mapped[int | None] = mapped_column(Integer)

    session: Mapped["SimulationSession"] = relationship(  # noqa: F821
        back_populates="decision_log", lazy="noload"
    )
    ai_feedback: Mapped["AIFeedback | None"] = relationship(  # noqa: F821
        lazy="noload", foreign_keys=[ai_feedback_id]
    )

    def __repr__(self) -> str:
        return f"<DecisionLog step={self.step_key} option={self.option_key}>"
