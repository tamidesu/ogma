"""
GET /briefs?profession_slug=doctor   — list available open-world briefs
GET /briefs/{brief_id}               — single brief (case file, NPC info, metadata)
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.schemas.common import ResponseEnvelope
from app.core.exceptions import NotFoundError
from app.db.models.profession import Profession
from app.db.models.scenario_brief import ScenarioBrief
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/briefs", tags=["briefs"])


def _brief_summary(brief: ScenarioBrief, profession_slug: str) -> dict:
    return {
        "id": str(brief.id),
        "slug": brief.slug,
        "title": brief.title,
        "profession_slug": profession_slug,
        "difficulty": brief.difficulty,
        "estimated_turns": brief.estimated_turns,
        "max_turns": brief.max_turns,
        "locale": brief.locale,
        "npc_display_name": (brief.npc_definition or {}).get("display_name", ""),
        "npc_role": (brief.npc_definition or {}).get("role", ""),
        "initial_suggested_actions": brief.initial_suggested_actions or [],
    }


def _brief_detail(brief: ScenarioBrief, profession_slug: str) -> dict:
    d = _brief_summary(brief, profession_slug)
    d["case_file_md"] = brief.case_file_md
    d["npc_definition"] = brief.npc_definition
    d["initial_world_state"] = brief.initial_world_state
    return d


@router.get("", response_model=ResponseEnvelope[list[dict]])
async def list_briefs(
    db: DBSession,
    current_user: CurrentUser,
    profession_slug: str = Query(..., description="Filter by profession slug"),
):
    stmt = (
        select(ScenarioBrief, Profession.slug)
        .join(Profession, Profession.id == ScenarioBrief.profession_id)
        .where(Profession.slug == profession_slug)
        .order_by(ScenarioBrief.difficulty.asc(), ScenarioBrief.created_at.asc())
    )
    rows = (await db.execute(stmt)).all()
    return ResponseEnvelope.ok([_brief_summary(b, slug) for b, slug in rows])


@router.get("/{brief_id}", response_model=ResponseEnvelope[dict])
async def get_brief(
    brief_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
):
    stmt = (
        select(ScenarioBrief, Profession.slug)
        .join(Profession, Profession.id == ScenarioBrief.profession_id)
        .where(ScenarioBrief.id == brief_id)
    )
    row = (await db.execute(stmt)).first()
    if not row:
        raise NotFoundError("Brief not found")
    brief, slug = row
    return ResponseEnvelope.ok(_brief_detail(brief, slug))
