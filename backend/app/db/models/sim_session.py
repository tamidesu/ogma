import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKey

SESSION_STATUSES = ("active", "paused", "completed", "abandoned")


class SimulationSession(Base, UUIDPrimaryKey):
    __tablename__ = "simulation_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'paused', 'completed', 'abandoned')",
            name="valid_status",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=False, index=True
    )
    scenario_version: Mapped[int] = mapped_column(default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False, index=True)
    current_step_key: Mapped[str] = mapped_column(String(100), nullable=False)

    # Full mutable simulation state — typed via SimSessionState Pydantic model
    state_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    final_score: Mapped[float | None] = mapped_column(Numeric(6, 2))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions", lazy="noload")  # noqa: F821
    decision_log: Mapped[list["DecisionLog"]] = relationship(  # noqa: F821
        back_populates="session", lazy="noload", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SimulationSession id={self.id} status={self.status}>"
