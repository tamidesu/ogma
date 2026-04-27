"""
NPCState — the unified NPC's persistent state for a single session.

The NPC has emotion (decays toward baseline each turn), a relationship
score with the user, a rolling memory window, and a current label that
the VisualDirector reads to pick avatars / scene moods.

One-to-one with simulation_sessions in the open-world flow.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NPCState(Base):
    __tablename__ = "npc_states"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("simulation_sessions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # FK to a logical NPCDefinition.id stored inside the brief's JSON;
    # kept as a plain string so briefs stay self-contained.
    definition_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # {"trust": 60, "fear": 30, "anger": 10, "hope": 50}
    emotion_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    relationship_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Rolling list of NPCMemoryItem dicts; capped at 12 in the orchestrator.
    memory_json: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Human-readable emotion label, e.g. "anxious_distressed". Drives visuals.
    current_label: Mapped[str | None] = mapped_column(String(80))

    # Avatar image_id currently active for this NPC (changes turn-to-turn).
    current_avatar_id: Mapped[str | None] = mapped_column(String(200))

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    session: Mapped["SimulationSession"] = relationship(lazy="noload")  # noqa: F821

    def __repr__(self) -> str:
        return f"<NPCState session={self.session_id} label={self.current_label}>"
