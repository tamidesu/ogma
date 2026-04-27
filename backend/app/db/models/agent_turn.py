"""
AgentTurn — one row per simulation turn in the open-world flow.

Captures the full trace produced by the agent pipeline, so that:
  • the UI can replay any session deterministically
  • debugging tools can inspect why an NPC reacted a given way
  • future eval pipelines can score agent quality offline
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKey


class AgentTurn(Base, UUIDPrimaryKey):
    __tablename__ = "agent_turns"
    __table_args__ = (UniqueConstraint("session_id", "turn_index", name="uq_turn_session_index"),)

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("simulation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Raw user input (free text, no preprocessing)
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    locale: Mapped[str] = mapped_column(String(10), default="kk", nullable=False)

    # Outputs from each agent — serialized dataclasses (see app/agents/schemas.py)
    intent_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    validation_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    npc_update_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    world_delta_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # ID into image_assets — what the VisualDirector chose for this turn
    image_id: Mapped[str | None] = mapped_column(String(200))

    # Mentor coach feedback is generated asynchronously; FK set on completion
    mentor_feedback_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_feedback.id"), nullable=True
    )

    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    termination_reason: Mapped[str | None] = mapped_column(String(50))  # success/failure/timeout

    # Latency metrics — useful for performance tuning
    pipeline_latency_ms: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    session: Mapped["SimulationSession"] = relationship(lazy="noload")  # noqa: F821
    mentor_feedback: Mapped["AIFeedback | None"] = relationship(  # noqa: F821
        lazy="noload", foreign_keys=[mentor_feedback_id]
    )

    def __repr__(self) -> str:
        return f"<AgentTurn session={self.session_id} #{self.turn_index}>"
