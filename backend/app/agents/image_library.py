"""
ImageLibrary — manifest loader + BM25-backed search for the VisualDirector.

Loads app/agents/images/manifest.json once at startup. Builds an in-memory
BM25 index per profession over the concatenation of (description, tags,
characters_present, scene_category, mood, world_flags_match).

Public surface:
  • get_library() -> ImageLibrary singleton
  • library.search(query, profession, scene_filter=None, top_k=3) -> list[ImageMatch]
  • library.fallback(profession) -> ImageMatch
  • library.upsert_to_db(db) -> int  (mirror manifest into image_assets)

The library is read-only at runtime; manifest changes require a restart.
"""
from __future__ import annotations

import json
import re
import string
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import structlog

from app.agents.schemas import ImageMatch

logger = structlog.get_logger(__name__)

# Reuse the same stopword list and tokenizer style as the legacy retriever
# so query behavior is consistent across the system.
_STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "this", "that", "these", "those", "it", "its", "they", "their",
    "and", "or", "but", "not", "if", "then", "so", "than", "more",
})


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[%s]" % re.escape(string.punctuation), " ", text)
    text = text.replace("_", " ").replace("-", " ")
    tokens = text.split()
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]


@dataclass(frozen=True)
class _ImageEntry:
    id: str
    file: str
    profession: str
    scene_category: str
    mood: str
    characters_present: list[str]
    world_flags_match: list[str]
    tags: list[str]
    description: str

    def searchable_text(self) -> str:
        return " ".join([
            self.description,
            " ".join(self.tags),
            " ".join(self.characters_present),
            self.scene_category,
            self.mood,
            " ".join(self.world_flags_match),
        ])


class ImageLibrary:
    MANIFEST_PATH: ClassVar[Path] = Path(__file__).parent / "images" / "manifest.json"
    STATIC_URL_PREFIX: ClassVar[str] = "/static/images/"
    MIN_SCORE: ClassVar[float] = 0.6
    FALLBACK_ID_FMT: ClassVar[str] = "{profession}.transition.neutral"

    def __init__(self):
        # profession -> (BM25Okapi-or-fallback, list[_ImageEntry])
        self._by_profession: dict[str, tuple] = {}
        # profession -> {scene_category: list[_ImageEntry]}
        self._by_scene: dict[str, dict[str, list[_ImageEntry]]] = {}
        # id -> entry
        self._by_id: dict[str, _ImageEntry] = {}
        self._loaded = False

    # ── loading ──────────────────────────────────────────────────────

    def load(self, manifest_path: Path | None = None) -> None:
        if self._loaded:
            return
        path = manifest_path or self.MANIFEST_PATH
        if not path.exists():
            logger.warning("image_manifest_missing", path=str(path))
            self._loaded = True
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        entries: list[_ImageEntry] = []
        for item in data.get("images", []):
            try:
                e = _ImageEntry(
                    id=item["id"],
                    file=item["file"],
                    profession=item["profession"],
                    scene_category=item["scene_category"],
                    mood=item["mood"],
                    characters_present=list(item.get("characters_present", [])),
                    world_flags_match=list(item.get("world_flags_match", [])),
                    tags=list(item.get("tags", [])),
                    description=item["description"],
                )
            except KeyError as ex:
                logger.warning("image_manifest_skipped_entry",
                               id=item.get("id", "?"), missing_key=str(ex))
                continue
            entries.append(e)
            self._by_id[e.id] = e

        # Group by profession + build indices
        from collections import defaultdict
        by_prof: dict[str, list[_ImageEntry]] = defaultdict(list)
        for e in entries:
            by_prof[e.profession].append(e)

        for prof, items in by_prof.items():
            tokenized = [_tokenize(e.searchable_text()) for e in items]
            try:
                from rank_bm25 import BM25Okapi
                idx = BM25Okapi(tokenized)
            except ImportError:
                idx = _LinearScanIndex(tokenized)
            self._by_profession[prof] = (idx, items)
            scene_buckets: dict[str, list[_ImageEntry]] = defaultdict(list)
            for e in items:
                scene_buckets[e.scene_category].append(e)
            self._by_scene[prof] = dict(scene_buckets)

        self._loaded = True
        logger.info("image_library_loaded",
                    professions=list(self._by_profession.keys()),
                    total=len(entries))

    # ── search ───────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        profession: str,
        scene_filter: str | None = None,
        top_k: int = 3,
    ) -> list[ImageMatch]:
        if not self._loaded:
            self.load()
        bundle = self._by_profession.get(profession)
        if not bundle:
            return []
        idx, items = bundle
        tokens = _tokenize(query)
        if not tokens:
            return []
        scores = idx.get_scores(tokens)
        ranked = []
        for score, e in zip(scores, items):
            if score <= 0:
                continue
            if scene_filter and e.scene_category != scene_filter:
                continue
            ranked.append((float(score), e))
        ranked.sort(key=lambda x: x[0], reverse=True)
        return [self._to_match(e, score) for score, e in ranked[:top_k]]

    def fallback(self, profession: str) -> ImageMatch:
        fid = self.FALLBACK_ID_FMT.format(profession=profession)
        e = self._by_id.get(fid)
        if e:
            return ImageMatch(
                image_id=e.id,
                url=self._url(e.file),
                alt_text=e.description,
                score=0.0,
                is_fallback=True,
            )
        # Last-ditch fallback — any image for the profession
        bundle = self._by_profession.get(profession)
        if bundle:
            e = bundle[1][0]
            return ImageMatch(
                image_id=e.id,
                url=self._url(e.file),
                alt_text=e.description,
                score=0.0,
                is_fallback=True,
            )
        # Truly empty library
        return ImageMatch(image_id="", url="", alt_text="", score=0.0, is_fallback=True)

    def get_by_id(self, image_id: str) -> ImageMatch | None:
        e = self._by_id.get(image_id)
        if not e:
            return None
        return ImageMatch(
            image_id=e.id,
            url=self._url(e.file),
            alt_text=e.description,
            score=1.0,
            is_fallback=False,
        )

    def has_loaded(self) -> bool:
        return self._loaded

    # ── DB mirror (called once at startup, idempotent) ───────────────

    async def upsert_to_db(self, db) -> int:
        """Mirror the manifest into the image_assets table. Idempotent."""
        if not self._loaded:
            self.load()
        from datetime import datetime, timezone

        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from app.db.models.image_asset import ImageAsset

        count = 0
        now = datetime.now(timezone.utc)
        for e in self._by_id.values():
            stmt = pg_insert(ImageAsset).values(
                id=e.id,
                file_path=e.file,
                profession_slug=e.profession,
                scene_category=e.scene_category,
                mood=e.mood,
                characters_present=e.characters_present,
                world_flags_match=e.world_flags_match,
                tags=e.tags,
                description=e.description,
                created_at=now,
            ).on_conflict_do_update(
                index_elements=[ImageAsset.id],
                set_={
                    "file_path": e.file,
                    "profession_slug": e.profession,
                    "scene_category": e.scene_category,
                    "mood": e.mood,
                    "characters_present": e.characters_present,
                    "world_flags_match": e.world_flags_match,
                    "tags": e.tags,
                    "description": e.description,
                },
            )
            await db.execute(stmt)
            count += 1
        await db.commit()
        logger.info("image_library_db_synced", rows=count)
        return count

    # ── helpers ──────────────────────────────────────────────────────

    def _url(self, file_path: str) -> str:
        return self.STATIC_URL_PREFIX + file_path.lstrip("/")

    def _to_match(self, e: _ImageEntry, score: float) -> ImageMatch:
        return ImageMatch(
            image_id=e.id,
            url=self._url(e.file),
            alt_text=e.description,
            score=score,
            is_fallback=False,
        )


class _LinearScanIndex:
    def __init__(self, tokenized: list[list[str]]):
        self._tokenized = tokenized

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        qset = set(query_tokens)
        out: list[float] = []
        for toks in self._tokenized:
            if not toks:
                out.append(0.0); continue
            tset = set(toks)
            inter = len(qset & tset)
            out.append(inter / max(len(qset), 1) if inter else 0.0)
        return out


# ── module singleton ────────────────────────────────────────────────

_library: ImageLibrary | None = None


def get_library() -> ImageLibrary:
    global _library
    if _library is None:
        _library = ImageLibrary()
        _library.load()
    return _library
