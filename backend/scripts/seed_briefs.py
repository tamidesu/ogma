"""
Seed scenario briefs from JSON files into the scenario_briefs table.

Idempotent — runs `INSERT ... ON CONFLICT DO UPDATE` keyed on (profession_id, slug),
so re-running picks up edits to the JSON files.

Usage:
    python -m scripts.seed_briefs                 # seed all briefs in scripts/briefs/
    python -m scripts.seed_briefs <file.json>     # seed a specific file
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models.profession import Profession
from app.db.models.scenario_brief import ScenarioBrief
from app.db.session import async_session_factory

logger = structlog.get_logger(__name__)

BRIEFS_DIR = Path(__file__).parent / "briefs"


async def _seed_one(payload: dict, profession_id) -> None:
    async with async_session_factory() as db:
        stmt = pg_insert(ScenarioBrief).values(
            profession_id=profession_id,
            slug=payload["slug"],
            title=payload["title"],
            case_file_md=payload["case_file_md"],
            initial_world_state=payload.get("initial_world_state", {}),
            success_criteria_jsonlogic=payload.get("success_criteria_jsonlogic"),
            failure_criteria_jsonlogic=payload.get("failure_criteria_jsonlogic"),
            timeout_resolution=payload.get("timeout_resolution"),
            max_turns=int(payload.get("max_turns", 12)),
            npc_definition=payload["npc_definition"],
            complication_pool=payload.get("complication_pool", []),
            knowledge_tags=payload.get("knowledge_tags", []),
            initial_suggested_actions=payload.get("initial_suggested_actions", []),
            difficulty=int(payload.get("difficulty", 3)),
            estimated_turns=int(payload.get("estimated_turns", 6)),
            locale=payload.get("locale", "kk"),
        ).on_conflict_do_update(
            index_elements=[ScenarioBrief.profession_id, ScenarioBrief.slug],
            set_={
                "title": payload["title"],
                "case_file_md": payload["case_file_md"],
                "initial_world_state": payload.get("initial_world_state", {}),
                "success_criteria_jsonlogic": payload.get("success_criteria_jsonlogic"),
                "failure_criteria_jsonlogic": payload.get("failure_criteria_jsonlogic"),
                "timeout_resolution": payload.get("timeout_resolution"),
                "max_turns": int(payload.get("max_turns", 12)),
                "npc_definition": payload["npc_definition"],
                "complication_pool": payload.get("complication_pool", []),
                "knowledge_tags": payload.get("knowledge_tags", []),
                "initial_suggested_actions": payload.get("initial_suggested_actions", []),
                "difficulty": int(payload.get("difficulty", 3)),
                "estimated_turns": int(payload.get("estimated_turns", 6)),
                "locale": payload.get("locale", "kk"),
            },
        )
        await db.execute(stmt)
        await db.commit()
    logger.info("brief_seeded", slug=payload["slug"])


async def _resolve_profession_id(slug: str):
    async with async_session_factory() as db:
        stmt = select(Profession.id).where(Profession.slug == slug)
        res = await db.execute(stmt)
        row = res.first()
        if not row:
            raise SystemExit(f"profession {slug!r} not found — run seed_scenarios.py first")
        return row[0]


async def main(targets: list[Path]) -> None:
    if not targets:
        targets = sorted(BRIEFS_DIR.glob("*.json"))
    if not targets:
        raise SystemExit(f"no briefs found in {BRIEFS_DIR}")
    for path in targets:
        payload = json.loads(path.read_text(encoding="utf-8"))
        profession_id = await _resolve_profession_id(payload["profession_slug"])
        await _seed_one(payload, profession_id)
    logger.info("seed_briefs_done", count=len(targets))


if __name__ == "__main__":
    args = [Path(a) for a in sys.argv[1:]]
    asyncio.run(main(args))
