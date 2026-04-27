"""
Shared dataclasses for the multi-agent pipeline.

Design notes:
  • All dataclasses are frozen — agents return new instances, never mutate.
  • All dataclasses are JSON-serializable via .to_dict() so they round-trip
    cleanly into Postgres JSONB columns and SSE event payloads.
  • Free-form fields (utterance, coach_note, descriptions) are plain strings
    in the scenario locale (Kazakh by default for the doctor MVP).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


Severity = Literal["minor", "moderate", "severe", "critical"]


# ─────────────────────────────────────────────────────────
# 0. Inputs
# ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class UserAction:
    """Free-text input from the user, plus the locale they typed it in."""
    raw_text: str
    locale: str = "kk"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────
# 1. ActionInterpreter output
# ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Intent:
    """Structured representation of what the user wants to do."""
    verb: str                                  # "order" | "ask" | "examine" | "console" | ...
    target: str                                # "patient.airway" | "blood_bank" | "family"
    parameters: dict[str, Any] = field(default_factory=dict)
    plausibility: float = 1.0                  # 0..1; Validator may downgrade
    requires_clarification: str | None = None  # if non-None, NPC asks user to clarify
    raw_paraphrase: str = ""                   # short echo for the UI strip

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────
# 2. DomainValidator output
# ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Citation:
    """Single retrieved knowledge chunk surfaced to the user."""
    source: str          # "ATLS 10th ed., ch.3" | "КК РК §32"
    snippet: str         # short excerpt (1–2 sentences max for the UI)
    tag: str = ""        # which knowledge_tag matched
    relevance: float = 0.0


@dataclass(frozen=True)
class ValidationResult:
    is_legal: bool
    is_standard_of_care: bool
    severity_if_wrong: Severity
    citations: list[Citation] = field(default_factory=list)
    coach_note: str = ""        # one-sentence rationale shown in the turn strip
    blocks_action: bool = False  # only true for severity in {severe, critical}

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


# ─────────────────────────────────────────────────────────
# 3. NPCDirector output + supporting types
# ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class NPCMemoryItem:
    """Rolling window entry — one per past turn, capped at 12."""
    turn_index: int
    user_intent_summary: str
    npc_response_summary: str
    emotion_at_time: dict[str, int]


@dataclass(frozen=True)
class NPCDefinition:
    """Static NPC persona, authored in a ScenarioBrief."""
    id: str
    display_name: str
    role: str
    backstory: str
    personality_traits: dict[str, int]   # Big-Five-ish, 0..100
    initial_emotion: dict[str, int]      # {trust, fear, anger, hope}
    voice_directives: str
    memory_seeds: list[str] = field(default_factory=list)
    avatar_image_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NPCUpdate:
    """What the NPCDirector returns each turn."""
    emotion_delta: dict[str, int]      # {"trust": -10, "fear": +20}
    relationship_delta: int            # added to long-arc relationship_score
    new_state_label: str               # e.g. "anxious_distressed" — drives visuals
    utterance: str                     # what the NPC says (in scenario locale)
    body_language: str                 # short phrase: "glances at the door"
    suggested_avatar_id: str = ""      # hint for the VisualDirector

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────
# 4. ConsequenceEngine output
# ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SkillXPGain:
    skill: str
    xp: int


@dataclass(frozen=True)
class WorldDelta:
    """Bounded mutation of world state produced by the ConsequenceEngine."""
    metric_delta: dict[str, float] = field(default_factory=dict)
    state_set: dict[str, Any] = field(default_factory=dict)
    time_advance_min: int = 0
    new_complication: dict[str, Any] | None = None
    skill_xp: list[SkillXPGain] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────
# 5. VisualDirector output
# ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ImageMatch:
    image_id: str
    url: str
    alt_text: str
    score: float = 0.0
    is_fallback: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ─────────────────────────────────────────────────────────
# 6. Aggregated turn result
# ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TurnResult:
    """Everything the orchestrator produces for one turn — payload for SSE & DB."""
    intent: Intent
    validation: ValidationResult
    npc_update: NPCUpdate
    world_delta: WorldDelta
    image: ImageMatch
    is_terminal: bool = False
    termination_reason: str | None = None  # "success" | "failure" | "timeout"
    pipeline_latency_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent.to_dict(),
            "validation": self.validation.to_dict(),
            "npc_update": self.npc_update.to_dict(),
            "world_delta": self.world_delta.to_dict(),
            "image": self.image.to_dict(),
            "is_terminal": self.is_terminal,
            "termination_reason": self.termination_reason,
            "pipeline_latency_ms": self.pipeline_latency_ms,
        }


# ─────────────────────────────────────────────────────────
# 7. Brief — passed to every agent as context
# ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ScenarioBriefData:
    """In-memory representation of a ScenarioBrief row, hydrated for agents."""
    id: str
    profession_slug: str
    slug: str
    title: str
    case_file_md: str
    initial_world_state: dict[str, Any]
    success_criteria_jsonlogic: dict[str, Any] | None
    failure_criteria_jsonlogic: dict[str, Any] | None
    timeout_resolution: str | None
    max_turns: int
    npc_definition: NPCDefinition
    complication_pool: list[dict[str, Any]]
    knowledge_tags: list[str]
    initial_suggested_actions: list[str]
    locale: str
