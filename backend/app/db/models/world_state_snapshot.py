"""
WorldStateSnapshot — append-only history of world state per session.

One row per turn (and one for turn 0, the initial state). Used for:
  • exact replay / debugging
  • the RetrospectiveTimeline UI on the results page
  • future analytics on world-state divergence between users
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKey


class WorldStateSnapshot(Base, UUIDPrimaryKey):
    __tablename__ = "world_state_snapshots"
    __table_args__ = (
        UniqueConstraint("session_id", "turn_index", name="uq_world_session_turn"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("simulation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    state_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    session: Mapped["SimulationSession"] = relationship(lazy="noload")  # noqa: F821

    def __repr__(self) -> str:
        return f"<WorldStateSnapshot session={self.session_id} turn={self.turn_index}>"
