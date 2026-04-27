"""
app.agents — multi-agent orchestrator for the open-world simulation.

Pipeline (per turn):

    UserAction
        │
        ▼
    ┌─────────────────────────┐
    │ 1. ActionInterpreter    │  free text → Intent (verb/target/params)
    └──────────┬──────────────┘
               ▼
    ┌─────────────────────────┐
    │ 2. DomainValidator      │  RAG-grounded plausibility + citations
    └──────────┬──────────────┘
               ▼
    ┌─────────────────────────┐
    │ 3. NPCDirector          │  emotion update + dialogue + body language
    └──────────┬──────────────┘
               ▼
    ┌─────────────────────────┐
    │ 4. ConsequenceEngine    │  world-state deltas + complications
    └──────────┬──────────────┘
               ▼
    ┌─────────────────────────┐
    │ 5. VisualDirector       │  picks an image from the curated library
    └──────────┬──────────────┘
               ▼
        TurnResult
        (streamed to client via SSE; MentorCoach runs async)

All agents are stateless: they read an immutable session snapshot and
return a structured dataclass. The TurnOrchestrator merges deltas under
a Redis lock keyed by session_id at the end of the turn.
"""
from app.agents.schemas import (
    UserAction, Intent, Citation, ValidationResult,
    NPCMemoryItem, NPCUpdate, WorldDelta, TurnResult,
    NPCDefinition, ScenarioBriefData, ImageMatch,
)

__all__ = [
    "UserAction", "Intent", "Citation", "ValidationResult",
    "NPCMemoryItem", "NPCUpdate", "WorldDelta", "TurnResult",
    "NPCDefinition", "ScenarioBriefData", "ImageMatch",
]
