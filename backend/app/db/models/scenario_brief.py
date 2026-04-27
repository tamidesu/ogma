"""
ScenarioBrief — open-world scenario definition for the agentic flow.

Replaces the rigid Step/Option content model for the new simulation mode.
A brief describes:
  • the case file (Markdown narrative the user reads at session start)
  • the initial world state (typed JSON)
  • success/failure criteria as JSONLogic predicates over world state
  • the unified NPC for the scenario (personality, voice, memory seeds)
  • a complication pool the ConsequenceEngine may sample from
  • which RAG knowledge tags are in scope for the DomainValidator
"""
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class ScenarioBrief(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "scenario_briefs"
    __table_args__ = (UniqueConstraint("profession_id", "slug", name="uq_brief_profession_slug"),)

    profession_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professions.id"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    case_file_md: Mapped[str] = mapped_column(Text, nullable=False)

    # Typed world state schema + initial values
    initial_world_state: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # JSONLogic predicates evaluated after every turn
    success_criteria_jsonlogic: Mapped[dict | None] = mapped_column(JSONB)
    failure_criteria_jsonlogic: Mapped[dict | None] = mapped_column(JSONB)

    timeout_resolution: Mapped[str | None] = mapped_column(Text)
    max_turns: Mapped[int] = mapped_column(Integer, default=12, nullable=False)

    # NPCDefinition serialized — see app/agents/schemas.py
    npc_definition: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Pool of complications the ConsequenceEngine may spawn (bounds the world)
    complication_pool: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Which RAG tags the DomainValidator should retrieve over for this brief
    knowledge_tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)

    # First-turn suggested actions (4 hand-authored chips, in scenario locale)
    initial_suggested_actions: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, nullable=False
    )

    # Difficulty 1..5 + estimated turns (display only)
    difficulty: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    estimated_turns: Mapped[int] = mapped_column(Integer, default=6, nullable=False)

    locale: Mapped[str] = mapped_column(String(10), default="kk", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    profession: Mapped["Profession"] = relationship(lazy="noload")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ScenarioBrief slug={self.slug} v{self.version}>"
