from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKey


class Profession(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "professions"

    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    icon_key: Mapped[str | None] = mapped_column(String(50))
    color_hex: Mapped[str | None] = mapped_column(String(7))   # e.g. "#34d399" — used by frontend
    difficulty_label: Mapped[str | None] = mapped_column(String(50))  # "Beginner" / "Advanced"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    scenarios: Mapped[list["ScenarioDef"]] = relationship(  # noqa: F821
        back_populates="profession", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<Profession slug={self.slug}>"
