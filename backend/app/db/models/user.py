import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class User(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    sessions: Mapped[list["SimulationSession"]] = relationship(  # noqa: F821
        back_populates="user", lazy="noload"
    )
    skill_profile: Mapped["SkillProfile | None"] = relationship(  # noqa: F821
        back_populates="user", uselist=False, lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
