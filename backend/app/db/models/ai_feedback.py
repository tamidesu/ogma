import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKey


class AIFeedback(Base, UUIDPrimaryKey):
    __tablename__ = "ai_feedback"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("simulation_sessions.id"), nullable=False, index=True
    )
    step_key: Mapped[str] = mapped_column(String(100), nullable=False)
    option_key: Mapped[str] = mapped_column(String(100), nullable=False)
    feedback_text: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str | None] = mapped_column(String(20))
    model_used: Mapped[str | None] = mapped_column(String(100))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Structured fields from JSON mode response
    key_insight: Mapped[str | None] = mapped_column(Text)
    coaching_question: Mapped[str | None] = mapped_column(Text)
    consequence_analysis: Mapped[str | None] = mapped_column(Text)
    alternative_path: Mapped[str | None] = mapped_column(Text)

    # Tone/quality metadata — useful for frontend badge and eval pipelines
    tone: Mapped[str | None] = mapped_column(String(50))         # "encouraging" | "critical" | "neutral"
    quality_score: Mapped[int | None] = mapped_column(Integer)   # 1-5, set by eval pipeline

    def __repr__(self) -> str:
        return f"<AIFeedback session={self.session_id} step={self.step_key}>"
