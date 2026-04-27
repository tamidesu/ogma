"""
VisualDirector — picks an image from the curated library for the new world state.

Pure retrieval, no LLM call. Algorithm:

  1. Infer scene_category from active world flags + NPC label.
     If the NPC just spoke and emotion-state is in {shocked, anxious, ...} and
     the world-flag `patient_informed_diagnosis=true` was just set, the scene
     is `exam_room`. If `phase=imaging` is active, prefer `imaging_lab`.
  2. Build a query string from: NPC label, body language, NPC characters_present
     hint, top 3 active world flags.
  3. ImageLibrary.search(query, profession, scene_filter=inferred_scene).
  4. If top score < MIN_SCORE → drop the scene_filter and re-search.
  5. If still empty → return library.fallback(profession).
  6. Optionally short-circuit when NPCDirector returned an explicit
     suggested_avatar_id that exists in the library AND we are in an
     "avatar moment" (NPC just delivered a strong utterance).

A small Redis-backed cache keyed by state-hash dedupes repeated
selections across turns when the world hasn't moved meaningfully.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import structlog

from app.agents.image_library import ImageLibrary, get_library
from app.agents.schemas import (
    ImageMatch, Intent, NPCUpdate, ScenarioBriefData, WorldDelta,
)

logger = structlog.get_logger(__name__)


# Scene heuristics — which world flags imply which scene_category.
# Order matters: earlier rules win.
_SCENE_RULES: list[tuple[str, callable]] = [
    ("imaging_lab",
     lambda flags, label, intent: any(k.startswith("imaging.") for k in flags)
                                  or intent.target.startswith("imaging.")),
    ("consultation_room",
     lambda flags, label, intent: flags.get("specialist_consulted") is True
                                  or intent.verb in {"consult", "refer", "huddle"}),
    ("er_trauma_bay",
     lambda flags, label, intent: flags.get("mass_casualty_active") is True),
    ("triage_zone",
     lambda flags, label, intent: flags.get("triage_protocol_activated") is True),
    ("icu",
     lambda flags, label, intent: flags.get("patient_intubated") is True),
    ("family_waiting_room",
     lambda flags, label, intent: intent.target == "family"
                                  or "family" in (label or "").lower()),
    ("exam_room",
     lambda flags, label, intent: True),  # Default for the doctor profession
]


class VisualDirector:
    AVATAR_MOMENT_LABELS = frozenset({
        "shocked_processing", "shocked_diagnosed",
        "calm_engaged", "calm_initial",
        "anxious_distressed", "anxious_waiting",
        "grateful_open", "relieved_warm",
        "peaceful_decided", "hostile_withdrawn",
    })

    def __init__(self, library: ImageLibrary | None = None, redis_client: Any = None):
        self._library = library or get_library()
        self._redis = redis_client  # optional; falls back to no-cache when None

    async def pick(
        self,
        intent: Intent,
        npc_update: NPCUpdate,
        world_delta: WorldDelta,
        brief: ScenarioBriefData,
        world_state_after: dict,
    ) -> ImageMatch:
        # ── 0. Cache lookup ──────────────────────────────────────────
        cache_key = self._cache_key(brief, npc_update, world_state_after)
        cached_id = await self._cache_get(cache_key)
        if cached_id:
            hit = self._library.get_by_id(cached_id)
            if hit:
                return hit

        # ── 1. Avatar-moment short-circuit ───────────────────────────
        if (
            npc_update.suggested_avatar_id
            and npc_update.new_state_label in self.AVATAR_MOMENT_LABELS
        ):
            hit = self._library.get_by_id(npc_update.suggested_avatar_id)
            if hit:
                await self._cache_set(cache_key, hit.image_id)
                return hit

        # ── 2. Infer scene category ──────────────────────────────────
        flat_flags = self._flatten_flags(world_state_after)
        scene_category = self._infer_scene(flat_flags, npc_update.new_state_label, intent)

        # ── 3. Build query ───────────────────────────────────────────
        query = self._build_query(npc_update, intent, flat_flags, brief)

        # ── 4. Search with scene_filter ──────────────────────────────
        results = self._library.search(
            query=query,
            profession=brief.profession_slug,
            scene_filter=scene_category,
            top_k=3,
        )

        # ── 5. Relax filter if too weak ──────────────────────────────
        if not results or results[0].score < ImageLibrary.MIN_SCORE:
            relaxed = self._library.search(
                query=query,
                profession=brief.profession_slug,
                scene_filter=None,
                top_k=3,
            )
            if relaxed and relaxed[0].score >= ImageLibrary.MIN_SCORE:
                results = relaxed

        # ── 6. Fallback ──────────────────────────────────────────────
        if not results:
            logger.info("visual_director_fallback",
                        profession=brief.profession_slug,
                        scene=scene_category, query=query[:80])
            chosen = self._library.fallback(brief.profession_slug)
        else:
            chosen = results[0]

        await self._cache_set(cache_key, chosen.image_id)
        return chosen

    # ── helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _flatten_flags(world_state: dict) -> dict[str, Any]:
        """Flatten {'flags': {'a': True}, 'phase': 'x'} → {'a': True, 'phase': 'x'}."""
        flat: dict[str, Any] = {}
        flags = world_state.get("flags") or {}
        if isinstance(flags, dict):
            flat.update(flags)
        time = world_state.get("time") or {}
        if isinstance(time, dict):
            flat.update(time)
        diag = world_state.get("diagnosis") or {}
        if isinstance(diag, dict):
            flat.update(diag)
        return flat

    @staticmethod
    def _infer_scene(flags: dict, label: str | None, intent: Intent) -> str:
        for category, rule in _SCENE_RULES:
            try:
                if rule(flags, label, intent):
                    return category
            except Exception:  # pragma: no cover — defensive
                continue
        return "exam_room"

    @staticmethod
    def _build_query(
        npc: NPCUpdate, intent: Intent, flags: dict, brief: ScenarioBriefData,
    ) -> str:
        active_flags = [k for k, v in flags.items() if v is True][:5]
        npc_id = brief.npc_definition.id
        parts = [
            (npc.new_state_label or "").replace("_", " "),
            npc.body_language or "",
            intent.target.replace(".", " "),
            " ".join(active_flags).replace("_", " "),
            npc_id.replace("_", " "),
        ]
        return " ".join(p for p in parts if p)

    @staticmethod
    def _cache_key(brief: ScenarioBriefData, npc: NPCUpdate, world: dict) -> str:
        payload = {
            "p": brief.profession_slug,
            "b": brief.slug,
            "l": npc.new_state_label,
            "f": sorted([k for k, v in (world.get("flags") or {}).items() if v]),
            "ph": (world.get("time") or {}).get("current_phase"),
        }
        h = hashlib.sha1(
            json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8"),
            usedforsecurity=False,
        ).hexdigest()[:16]
        return f"visual:{h}"

    async def _cache_get(self, key: str) -> str | None:
        if not self._redis:
            return None
        try:
            val = await self._redis.get(key)
            return val.decode() if isinstance(val, bytes) else val
        except Exception:  # pragma: no cover — defensive
            return None

    async def _cache_set(self, key: str, image_id: str) -> None:
        if not self._redis or not image_id:
            return
        try:
            await self._redis.set(key, image_id, ex=120)
        except Exception:  # pragma: no cover — defensive
            return
