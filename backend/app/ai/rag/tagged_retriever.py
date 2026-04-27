"""
TaggedMarkdownRetriever — BM25 over a structured markdown corpus.

Difference from BM25Retriever:
  • Loads .md files (recursively) under knowledge/{profession}/...
  • Each file has YAML-style frontmatter declaring `tag`, `title`, `source_citation`,
    `applies_to_scenarios`, `locale`.
  • Each H2 section becomes a separate retrievable chunk that inherits the file's metadata.
  • query() returns RetrievedChunk objects (text + citation + tag + score), not strings.
  • Filters by `knowledge_tags` (a list of tags the brief restricts retrieval to).

The legacy BM25Retriever in bm25_retriever.py is preserved for the existing
guided-mode flow. The two retrievers can coexist.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import structlog

from app.ai.rag.retriever import RetrievedChunk

logger = structlog.get_logger(__name__)


# Stopwords — same set as the legacy BM25Retriever, keep in sync.
_STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "this", "that", "these", "those", "it", "its", "they", "their",
    "and", "or", "but", "not", "if", "then", "so", "than", "more",
    # Russian
    "это", "не", "и", "в", "на", "с", "из", "что", "как", "при",
    "или", "но", "же", "для", "по", "от", "до", "за", "к",
})


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    tokens = text.split()
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 2]


_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(raw: str) -> tuple[dict, str]:
    """Tiny YAML-ish frontmatter parser — supports flat key:value and key:[a, b]."""
    m = _FRONTMATTER_RE.match(raw)
    if not m:
        return {}, raw
    body = raw[m.end():]
    meta: dict = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        # strip surrounding quotes
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        # list literal: [a, b, "c"]
        if val.startswith("[") and val.endswith("]"):
            inside = val[1:-1].strip()
            if not inside:
                meta[key] = []
            else:
                items = [s.strip().strip("\"'") for s in inside.split(",")]
                meta[key] = [s for s in items if s]
        else:
            meta[key] = val
    return meta, body


@dataclass(frozen=True)
class _IndexedChunk:
    text: str
    title: str       # H2 heading
    tag: str
    citation: str
    locale: str
    profession: str


class TaggedMarkdownRetriever:
    """BM25 over chunked markdown with frontmatter-derived citations."""

    KNOWLEDGE_DIR: ClassVar[Path] = Path(__file__).parent / "knowledge"

    def __init__(self):
        # profession -> (BM25 index, list[_IndexedChunk])
        self._indices: dict[str, tuple] = {}
        self._loaded = False

    # ── loading ──────────────────────────────────────────────────────

    def load_all(self) -> None:
        if self._loaded:
            return
        for prof_dir in self.KNOWLEDGE_DIR.iterdir():
            if not prof_dir.is_dir():
                continue
            try:
                self._load_profession(prof_dir)
            except Exception as e:  # pragma: no cover — defensive
                logger.error("tagged_rag_load_failed",
                             profession=prof_dir.name, error=str(e))
        self._loaded = True
        logger.info("tagged_rag_loaded", professions=list(self._indices.keys()))

    def _load_profession(self, prof_dir: Path) -> None:
        chunks: list[_IndexedChunk] = []
        for md_path in prof_dir.rglob("*.md"):
            raw = md_path.read_text(encoding="utf-8")
            meta, body = _parse_frontmatter(raw)
            tag = meta.get("tag") or f"{prof_dir.name}.{md_path.stem}"
            citation = meta.get("source_citation") or md_path.name
            locale = meta.get("locale", "en")
            for title, text in self._split_h2_sections(body):
                if len(text) < 40:
                    continue
                chunks.append(_IndexedChunk(
                    text=text.strip(),
                    title=title.strip(),
                    tag=tag,
                    citation=citation,
                    locale=locale,
                    profession=prof_dir.name,
                ))

        if not chunks:
            logger.warning("tagged_rag_empty_profession", profession=prof_dir.name)
            return

        try:
            from rank_bm25 import BM25Okapi
            tokenized = [_tokenize(c.text + " " + c.title) for c in chunks]
            index = BM25Okapi(tokenized)
            self._indices[prof_dir.name] = (index, chunks)
            logger.debug("tagged_rag_index_built",
                         profession=prof_dir.name, chunks=len(chunks))
        except ImportError:
            # Fall back to a trivial linear-scan index — useful in tests/sandbox
            # without the rank_bm25 dependency.
            self._indices[prof_dir.name] = (_LinearScanIndex(chunks), chunks)
            logger.warning("rank_bm25_unavailable_using_linear_scan",
                           profession=prof_dir.name)

    @staticmethod
    def _split_h2_sections(body: str) -> list[tuple[str, str]]:
        """Split body markdown on '## ' headings. Pre-heading text is dropped."""
        parts = re.split(r"^##\s+(.+?)\s*$", body, flags=re.MULTILINE)
        # parts = [pre_text, title1, body1, title2, body2, ...]
        sections: list[tuple[str, str]] = []
        for i in range(1, len(parts), 2):
            title = parts[i]
            text = parts[i + 1] if i + 1 < len(parts) else ""
            sections.append((title, text))
        return sections

    # ── query ────────────────────────────────────────────────────────

    def query(
        self,
        text: str,
        profession: str,
        knowledge_tags: list[str] | None = None,
        top_k: int = 3,
    ) -> list[RetrievedChunk]:
        if profession not in self._indices:
            return []
        index, chunks = self._indices[profession]
        tokens = _tokenize(text)
        if not tokens:
            return []
        scores = index.get_scores(tokens)
        # Pair scores with chunks, optionally filter by tag, sort, take top_k
        ranked: list[tuple[float, _IndexedChunk]] = []
        for score, chunk in zip(scores, chunks):
            if score <= 0:
                continue
            if knowledge_tags and chunk.tag not in knowledge_tags:
                continue
            ranked.append((score, chunk))
        ranked.sort(key=lambda x: x[0], reverse=True)
        out: list[RetrievedChunk] = []
        for score, c in ranked[:top_k]:
            out.append(RetrievedChunk(
                text=c.text,
                citation=c.citation,
                tag=c.tag,
                score=float(score),
                title=c.title,
            ))
        return out

    def is_ready(self) -> bool:
        return self._loaded and len(self._indices) > 0


class _LinearScanIndex:
    """Trivial fallback when rank_bm25 isn't installed.

    Computes a degenerate score = (matched_tokens / chunk_tokens). Good enough
    for tests; production always has rank_bm25 installed via pyproject.toml.
    """
    def __init__(self, chunks: list[_IndexedChunk]):
        self._tokenized = [_tokenize(c.text + " " + c.title) for c in chunks]

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        qset = set(query_tokens)
        scores: list[float] = []
        for toks in self._tokenized:
            if not toks:
                scores.append(0.0); continue
            tset = set(toks)
            inter = len(qset & tset)
            if inter == 0:
                scores.append(0.0); continue
            scores.append(inter / max(len(qset), 1))
        return scores


# ── module singleton ────────────────────────────────────────────────

_retriever: TaggedMarkdownRetriever | None = None


def get_tagged_retriever() -> TaggedMarkdownRetriever:
    global _retriever
    if _retriever is None:
        _retriever = TaggedMarkdownRetriever()
        _retriever.load_all()
    return _retriever
