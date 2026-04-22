import uuid

from sqlalchemy import (
    Boolean, ForeignKey, Integer, SmallInteger,
    String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class ScenarioDef(Base, UUIDPrimaryKey, TimestampMixin):
    """Scenario definition — immutable content, versioned."""
    __tablename__ = "scenarios"
    __table_args__ = (UniqueConstraint("profession_id", "slug"),)

    profession_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professions.id"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1-5
    estimated_steps: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    initial_metrics: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    initial_state: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    profession: Mapped["Profession"] = relationship(back_populates="scenarios", lazy="noload")  # noqa: F821
    steps: Mapped[list["StepDef"]] = relationship(
        back_populates="scenario",
        order_by="StepDef.sort_order",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    transitions: Mapped[list["StepTransition"]] = relationship(
        back_populates="scenario", lazy="noload", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ScenarioDef slug={self.slug} v{self.version}>"


class StepDef(Base, UUIDPrimaryKey):
    """Single step within a scenario."""
    __tablename__ = "steps"
    __table_args__ = (UniqueConstraint("scenario_id", "step_key"),)

    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    step_key: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    context_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), default="decision", nullable=False)
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)

    scenario: Mapped["ScenarioDef"] = relationship(back_populates="steps", lazy="noload")
    options: Mapped[list["OptionDef"]] = relationship(
        back_populates="step",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<StepDef key={self.step_key}>"


class OptionDef(Base, UUIDPrimaryKey):
    """Decision option within a step."""
    __tablename__ = "decision_options"
    __table_args__ = (UniqueConstraint("step_id", "option_key"),)

    step_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("steps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    option_key: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Effects applied when this option is chosen (list of effect objects)
    effects: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    # Conditions that must be true for this option to appear
    preconditions: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    next_step_key: Mapped[str | None] = mapped_column(String(100))

    step: Mapped["StepDef"] = relationship(back_populates="options", lazy="noload")

    def __repr__(self) -> str:
        return f"<OptionDef key={self.option_key}>"


class StepTransition(Base, UUIDPrimaryKey):
    """Explicit conditional transitions for complex branching."""
    __tablename__ = "step_transitions"

    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_step_key: Mapped[str] = mapped_column(String(100), nullable=False)
    condition: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    to_step_key: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    scenario: Mapped["ScenarioDef"] = relationship(back_populates="transitions", lazy="noload")
