import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKey


class SkillProfile(Base, UUIDPrimaryKey):
    __tablename__ = "skill_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    xp_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="skill_profile", lazy="noload")  # noqa: F821
    skill_scores: Mapped[list["SkillScore"]] = relationship(
        back_populates="profile", lazy="noload", cascade="all, delete-orphan"
    )
    completed_scenarios: Mapped[list["CompletedScenario"]] = relationship(
        back_populates="profile", lazy="noload", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SkillProfile user={self.user_id} level={self.level} xp={self.xp_total}>"


class SkillScore(Base, UUIDPrimaryKey):
    __tablename__ = "skill_scores"
    __table_args__ = (UniqueConstraint("skill_profile_id", "profession_id", "skill_key"),)

    skill_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_profiles.id"), nullable=False, index=True
    )
    profession_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("professions.id"), nullable=False
    )
    skill_key: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    profile: Mapped["SkillProfile"] = relationship(back_populates="skill_scores", lazy="noload")

    def __repr__(self) -> str:
        return f"<SkillScore skill={self.skill_key} score={self.score}>"


class CompletedScenario(Base, UUIDPrimaryKey):
    __tablename__ = "completed_scenarios"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=False
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("simulation_sessions.id"), nullable=False
    )
    skill_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("skill_profiles.id"), nullable=False
    )
    final_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    profile: Mapped["SkillProfile"] = relationship(back_populates="completed_scenarios", lazy="noload")

    def __repr__(self) -> str:
        return f"<CompletedScenario scenario={self.scenario_id} score={self.final_score}>"
