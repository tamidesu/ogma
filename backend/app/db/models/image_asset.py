"""
ImageAsset — the curated image library mirrored into Postgres.

Source of truth is app/agents/images/manifest.json (so designers can
edit it without touching the DB). On startup, the manifest is loaded
into this table for fast tag/full-text search by the VisualDirector.

The id matches the manifest's `id` field (e.g. "doctor.exam_room.patient_anxious").
"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ImageAsset(Base):
    __tablename__ = "image_assets"

    id: Mapped[str] = mapped_column(String(200), primary_key=True)
    file_path: Mapped[str] = mapped_column(String(400), nullable=False)
    profession_slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    scene_category: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    mood: Mapped[str] = mapped_column(String(40), nullable=False)
    characters_present: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, nullable=False
    )
    # Flags whose presence in world state makes this image a good match.
    # Match strings can be a key ("mass_casualty_active") or key=value pair.
    world_flags_match: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, nullable=False
    )
    tags: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Search corpus — in MVP we keep BM25 in-process via the same retriever
    # used for RAG. A GIN tsvector can be added later if needed.

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ImageAsset id={self.id}>"
