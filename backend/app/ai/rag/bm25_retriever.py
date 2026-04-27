"""
BM25Retriever — keyword-based retrieval using rank_bm25.

No external API, no heavy ML models, no GPU.
BM25 (Okapi BM25) is a robust, battle-tested ranking algorithm used by
Elasticsearch and most search engines as their baseline.

Knowledge bases are plain .txt files — one paragraph per entry (blank-line separated).
Built at application startup, held in memory.
"""
import re
import string
from pathlib import Path
from typing import ClassVar

import structlog

from app.ai.rag.retriever import Retriever

logger = structlog.get_logger(__name__)

# Stopwords — English + Russian common words
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
    text = re.sub(r"[%s]" % re.escape(string.punctuation), " ", text)
    tokens = text.split()
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 2]


class BM25Retriever(Retriever):
    """
    Per-profession BM25 index.
    Each profession has its own index built from its knowledge base file.
    """

    KNOWLEDGE_DIR: ClassVar[Path] = Path(__file__).parent / "knowledge"

    def __init__(self):
        # profession_slug → (BM25 index, list of paragraph strings)
        self._indices: dict[str, tuple] = {}
        self._loaded = False

    def load_all(self) -> None:
        """Call once at application startup."""
        if self._loaded:
            return

        loaded_count = 0
        for kb_file in self.KNOWLEDGE_DIR.glob("*.txt"):
            profession_slug = kb_file.stem
            try:
                self._load_profession(profession_slug, kb_file)
                loaded_count += 1
            except Exception as e:
                logger.error("rag_load_failed", profession=profession_slug, error=str(e))

        self._loaded = True
        logger.info("rag_loaded", profession_count=loaded_count)

    def _load_profession(self, slug: str, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        # Split on blank lines → paragraphs
        raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

        # Each paragraph becomes a retrievable chunk
        # Strip the ALL-CAPS topic header (e.g. "INCIDENT RESPONSE:") for display
        chunks: list[str] = []
        for para in raw_paragraphs:
            # Keep header for context, but clean it for display
            chunks.append(para)

        tokenized = [_tokenize(chunk) for chunk in chunks]

        # Build BM25 index
        try:
            from rank_bm25 import BM25Plus
            index = BM25Plus(tokenized)
            self._indices[slug] = (index, chunks)
            logger.debug("rag_index_built", profession=slug, chunks=len(chunks))
        except ImportError:
            logger.warning("rank_bm25_not_installed", profession=slug)

    def query(self, text: str, filters: dict, top_k: int = 3) -> list[str]:
        profession = filters.get("profession", "")
        if profession not in self._indices:
            return []

        index, chunks = self._indices[profession]
        query_tokens = _tokenize(text)
        if not query_tokens:
            return []

        scores = index.get_scores(query_tokens)
        # Get top_k indices by score, excluding zero-score
        ranked = sorted(
            [(score, i) for i, score in enumerate(scores) if score > 0],
            reverse=True,
        )[:top_k]

        results = []
        for score, idx in ranked:
            chunk = chunks[idx]
            # Return just the content (strip the TOPIC: prefix header for cleanliness)
            match = re.match(r"^[A-Z\s\-–—]+:\s*", chunk)
            if match:
                topic = match.group(0).rstrip(": ").title()
                body = chunk[match.end():]
                results.append(f"[{topic}] {body}")
            else:
                results.append(chunk)

        return results

    def is_ready(self) -> bool:
        return self._loaded and len(self._indices) > 0


# Module-level singleton — initialised at app startup
_retriever: BM25Retriever | None = None


def get_retriever() -> BM25Retriever:
    global _retriever
    if _retriever is None:
        _retriever = BM25Retriever()
        _retriever.load_all()
    return _retriever
