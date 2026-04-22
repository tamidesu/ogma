"""Unit tests for BM25Retriever."""
import tempfile
from pathlib import Path

import pytest

from app.ai.rag.bm25_retriever import BM25Retriever, _tokenize


class TestTokenize:

    def test_lowercases_and_strips_punctuation(self):
        tokens = _tokenize("Hello, World!")
        assert "hello" in tokens
        assert "world" in tokens

    def test_removes_stopwords(self):
        tokens = _tokenize("the incident is a critical failure")
        assert "the" not in tokens
        assert "is" not in tokens
        assert "a" not in tokens
        assert "incident" in tokens
        assert "critical" in tokens
        assert "failure" in tokens

    def test_removes_short_tokens(self):
        tokens = _tokenize("go to the API")
        assert "go" not in tokens  # len 2 stripped
        assert "to" not in tokens
        assert "api" in tokens

    def test_empty_string(self):
        assert _tokenize("") == []

    def test_russian_stopwords_removed(self):
        tokens = _tokenize("это не правильно для системы")
        assert "это" not in tokens
        assert "не" not in tokens
        assert "правильно" in tokens


class TestBM25Retriever:

    def _make_retriever_with_content(self, content: str, slug: str = "test_prof") -> BM25Retriever:
        retriever = BM25Retriever()
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_file = Path(tmpdir) / f"{slug}.txt"
            kb_file.write_text(content, encoding="utf-8")
            retriever.KNOWLEDGE_DIR = Path(tmpdir)
            retriever.load_all()
        return retriever

    def test_not_ready_before_load(self):
        retriever = BM25Retriever()
        assert not retriever.is_ready()

    def test_ready_after_load_with_content(self):
        content = "INCIDENT RESPONSE: Rollback early to minimize user impact.\n\nTECHNICAL DEBT: Every shortcut creates future obligations."
        retriever = self._make_retriever_with_content(content)
        assert retriever.is_ready()

    def test_query_returns_relevant_results(self):
        content = "INCIDENT RESPONSE: Rollback early to minimize user impact and restore service.\n\nTECHNICAL DEBT: Every shortcut creates future obligations in the codebase."
        retriever = self._make_retriever_with_content(content, "test_prof")
        results = retriever.query("rollback incident restore", filters={"profession": "test_prof"}, top_k=2)
        assert len(results) >= 1
        assert any("rollback" in r.lower() or "incident" in r.lower() for r in results)

    def test_query_returns_empty_for_unknown_profession(self):
        content = "INCIDENT: Some content here."
        retriever = self._make_retriever_with_content(content, "test_prof")
        results = retriever.query("incident", filters={"profession": "nonexistent"}, top_k=3)
        assert results == []

    def test_query_returns_empty_when_no_matches(self):
        content = "INCIDENT RESPONSE: Rollback early to minimize user impact."
        retriever = self._make_retriever_with_content(content, "test_prof")
        results = retriever.query("xyzzy frobnicator", filters={"profession": "test_prof"}, top_k=3)
        assert results == []

    def test_topic_header_stripped_from_output(self):
        content = "INCIDENT RESPONSE: Always rollback before investigating the root cause in production."
        retriever = self._make_retriever_with_content(content, "test_prof")
        results = retriever.query("rollback production", filters={"profession": "test_prof"}, top_k=1)
        assert len(results) == 1
        # Should have [Topic] prefix format
        assert results[0].startswith("[")

    def test_load_all_idempotent(self):
        content = "INCIDENT: Some content here about incidents and responses."
        retriever = self._make_retriever_with_content(content, "test_prof")
        # Second load should be no-op
        retriever.load_all()
        assert retriever.is_ready()

    def test_top_k_limits_results(self):
        content = "\n\n".join([
            "TOPIC A: First chunk about rollback and incidents and production failures.",
            "TOPIC B: Second chunk about rollback and incidents and production deployments.",
            "TOPIC C: Third chunk about rollback and incidents and production systems.",
            "TOPIC D: Fourth chunk about rollback and incidents and production alerts.",
        ])
        retriever = self._make_retriever_with_content(content, "test_prof")
        results = retriever.query("rollback incident production", filters={"profession": "test_prof"}, top_k=2)
        assert len(results) <= 2
