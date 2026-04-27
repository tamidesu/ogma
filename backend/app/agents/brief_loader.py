"""
BriefLoader — hydrates ScenarioBriefData from JSON files or DB rows.

Two entry points:
  • load_from_file(path)        — used by the seed script and tests
  • load_from_db(brief_id, db)  — used by the orchestrator at session start

Both return the same immutable ScenarioBriefData (with its NPCDefinition
already nested as a typed dataclass). The JSON file format is the source
of truth — DB rows are a mirror, populated by scripts/seed_briefs.py.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.schemas import NPCDefinition, ScenarioBriefData


def _hydrate_npc(d: dict[str, Any]) -> NPCDefinition:
    return NPCDefinition(
        id=d["id"],
        display_name=d["display_name"],
        role=d["role"],
        backstory=d["backstory"],
        personality_traits=d.get("personality_traits", {}),
        initial_emotion=d.get("initial_emotion", {}),
        voice_directives=d.get("voice_directives", ""),
        memory_seeds=list(d.get("memory_seeds", [])),
        avatar_image_id=d.get("avatar_image_id", ""),
    )


def _from_payload(payload: dict[str, Any], *, brief_id: str = "") -> ScenarioBriefData:
    """Shared hydration logic — used by both file and DB loaders."""
    return ScenarioBriefData(
        id=brief_id or payload.get("id", payload.get("slug", "")),
        profession_slug=payload["profession_slug"],
        slug=payload["slug"],
        title=payload["title"],
        case_file_md=payload["case_file_md"],
        initial_world_state=payload.get("initial_world_state", {}),
        success_criteria_jsonlogic=payload.get("success_criteria_jsonlogic"),
        failure_criteria_jsonlogic=payload.get("failure_criteria_jsonlogic"),
        timeout_resolution=payload.get("timeout_resolution"),
        max_turns=int(payload.get("max_turns", 12)),
        npc_definition=_hydrate_npc(payload["npc_definition"]),
        complication_pool=list(payload.get("complication_pool", [])),
        knowledge_tags=list(payload.get("knowledge_tags", [])),
        initial_suggested_actions=list(payload.get("initial_suggested_actions", [])),
        locale=payload.get("locale", "kk"),
    )


def load_from_file(path: str | Path) -> ScenarioBriefData:
    """Load a brief from a JSON file on disk."""
    raw = Path(path).read_text(encoding="utf-8")
    payload = json.loads(raw)
    return _from_payload(payload, brief_id=payload.get("slug", ""))


async def load_from_db(brief_id: UUID, db: AsyncSession) -> ScenarioBriefData | None:
    """Load a brief from the scenario_briefs table."""
    # Local import keeps this module importable in unit tests that don't
    # bring up the full SQLAlchemy registry.
    from app.db.models.scenario_brief import ScenarioBrief
    from app.db.models.profession import Profession

    stmt = (
        select(ScenarioBrief, Profession.slug)
        .join(Profession, Profession.id == ScenarioBrief.profession_id)
        .where(ScenarioBrief.id == brief_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        return None
    brief, profession_slug = row

    payload: dict[str, Any] = {
        "id": str(brief.id),
        "profession_slug": profession_slug,
        "slug": brief.slug,
        "title": brief.title,
        "case_file_md": brief.case_file_md,
        "initial_world_state": brief.initial_world_state,
        "success_criteria_jsonlogic": brief.success_criteria_jsonlogic,
        "failure_criteria_jsonlogic": brief.failure_criteria_jsonlogic,
        "timeout_resolution": brief.timeout_resolution,
        "max_turns": brief.max_turns,
        "npc_definition": brief.npc_definition,
        "complication_pool": brief.complication_pool,
        "knowledge_tags": brief.knowledge_tags,
        "initial_suggested_actions": brief.initial_suggested_actions,
        "locale": brief.locale,
    }
    return _from_payload(payload, brief_id=str(brief.id))
