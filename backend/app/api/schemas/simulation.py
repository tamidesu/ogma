from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ── Professions ───────────────────────────────────────────

class ProfessionResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None
    icon_key: str | None
    color_hex: str | None
    difficulty_label: str | None

    model_config = {"from_attributes": True}


class ScenarioSummaryResponse(BaseModel):
    id: UUID
    slug: str
    title: str
    description: str
    difficulty: int
    estimated_steps: int
    tags: list[str]

    model_config = {"from_attributes": True}


# ── Session ───────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    scenario_id: UUID


class OptionInfo(BaseModel):
    option_key: str
    label: str
    description: str | None
    is_available: bool  # False when preconditions not met


class StepInfo(BaseModel):
    step_key: str
    title: str
    narrative: str
    step_type: str
    available_options: list[OptionInfo]


class SessionResponse(BaseModel):
    session_id: UUID
    status: str
    scenario_id: UUID
    current_step: StepInfo | None
    metrics: dict[str, float]
    step_count: int
    started_at: str


class SessionSummaryResponse(BaseModel):
    session_id: UUID
    scenario_id: UUID
    status: str
    final_score: float | None
    started_at: str
    completed_at: str | None


# ── Decision ──────────────────────────────────────────────

class MakeDecisionRequest(BaseModel):
    option_key: str = Field(min_length=1, max_length=100)
    time_spent_sec: int | None = Field(None, ge=0, le=3600)


class SkillEarned(BaseModel):
    skill: str
    xp_gained: float


class AIFeedbackResponse(BaseModel):
    text: str | None
    generated: bool
    tone: str | None = None
    key_insight: str | None = None
    coaching_question: str | None = None
    consequence_analysis: str | None = None
    alternative_path: str | None = None


class DecisionResponse(BaseModel):
    decision_id: UUID
    option_key: str
    effects_applied: list[dict]
    metrics_before: dict[str, float]
    metrics_after: dict[str, float]
    step_score: float
    next_step: StepInfo | None
    is_terminal: bool
    final_score: float | None
    skills_earned: list[SkillEarned]
    xp_gained: int
    leveled_up: bool
    ai_feedback: AIFeedbackResponse


# ── History ───────────────────────────────────────────────

class DecisionHistoryItem(BaseModel):
    id: UUID
    step_key: str
    option_key: str
    metrics_before: dict[str, float]
    metrics_after: dict[str, float]
    effects_applied: list[dict]
    decided_at: str
    time_spent_sec: int | None
    ai_feedback: AIFeedbackResponse | None


# ── Progress ──────────────────────────────────────────────

class SkillScoreItem(BaseModel):
    profession_id: UUID
    skill_key: str
    score: float


class ProgressResponse(BaseModel):
    level: int
    xp_total: int
    xp_to_next_level: int
    skill_scores: list[SkillScoreItem]
    scenarios_completed: int


# ── AI Feedback poll ──────────────────────────────────────

class FeedbackPollResponse(BaseModel):
    decision_id: UUID
    ready: bool
    feedback: AIFeedbackResponse | None
