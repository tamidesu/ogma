"""Unit tests for GroqAdapter._parse_structured_response and JSON fallback."""
import pytest

from app.ai.groq_adapter import _parse_structured_response
from app.ai.provider_adapter import StructuredFeedback


class TestParseStructuredResponse:

    def test_parses_valid_json(self):
        raw = """{
            "feedback": "You made a solid decision here.",
            "key_insight": "Speed matters in incidents.",
            "coaching_question": "What signals would have led you to investigate first?",
            "consequence_analysis": "Fast rollbacks protect user trust.",
            "tone": "encouraging",
            "alternative_path": "Investigating first could have added context."
        }"""
        result = _parse_structured_response(raw)
        assert isinstance(result, StructuredFeedback)
        assert result.feedback == "You made a solid decision here."
        assert result.key_insight == "Speed matters in incidents."
        assert result.coaching_question == "What signals would have led you to investigate first?"
        assert result.consequence_analysis == "Fast rollbacks protect user trust."
        assert result.tone == "encouraging"
        assert result.alternative_path == "Investigating first could have added context."

    def test_strips_markdown_fences(self):
        raw = "```json\n{\"feedback\": \"Good call.\", \"key_insight\": \"X\", \"coaching_question\": \"Q?\", \"consequence_analysis\": \"C.\", \"tone\": \"neutral\"}\n```"
        result = _parse_structured_response(raw)
        assert result.feedback == "Good call."
        assert result.tone == "neutral"

    def test_falls_back_on_invalid_json(self):
        raw = "This is not JSON at all. Just plain text feedback."
        result = _parse_structured_response(raw)
        assert isinstance(result, StructuredFeedback)
        assert result.feedback == raw[:600]
        assert result.tone == "neutral"
        assert result.key_insight == ""

    def test_handles_partial_json(self):
        raw = '{"feedback": "Partial response.", "tone": "critical"}'
        result = _parse_structured_response(raw)
        assert result.feedback == "Partial response."
        assert result.tone == "critical"
        assert result.key_insight == ""  # missing field → empty string

    def test_handles_empty_string(self):
        result = _parse_structured_response("")
        assert isinstance(result, StructuredFeedback)
        assert result.tone == "neutral"

    def test_handles_none_values_in_json(self):
        raw = '{"feedback": null, "key_insight": "X", "coaching_question": null, "consequence_analysis": "C", "tone": "analytical"}'
        result = _parse_structured_response(raw)
        # None → "None" via str(), not ideal but stable
        assert result.key_insight == "X"
        assert result.tone == "analytical"

    def test_alternative_path_defaults_to_empty(self):
        raw = '{"feedback": "Good.", "key_insight": "X", "coaching_question": "Q?", "consequence_analysis": "C.", "tone": "neutral"}'
        result = _parse_structured_response(raw)
        assert result.alternative_path == ""
