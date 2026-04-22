"""Unit tests for PromptBuilder."""
import pytest

from app.ai.prompt_builder import DecisionHistoryItem, PromptBuilder, PromptContext


def _make_context(**overrides) -> PromptContext:
    defaults = dict(
        profession_slug="software_engineer",
        step_key="step_1",
        step_title="Production Incident",
        step_narrative="A critical service is down. What do you do?",
        step_context_data={"severity": "P0", "affected_users": 5000},
        option_chosen_key="rollback",
        option_chosen_label="Rollback immediately",
        option_description="Revert the last deployment",
        all_options=[
            {"option_key": "rollback", "label": "Rollback immediately", "description": ""},
            {"option_key": "patch", "label": "Push a hotfix", "description": ""},
            {"option_key": "investigate", "label": "Investigate first", "description": ""},
        ],
        metrics_before={"risk": 70.0, "reputation": 60.0, "team_morale": 50.0},
        metrics_after={"risk": 30.0, "reputation": 65.0, "team_morale": 55.0},
        effects_applied=[{"type": "metric_delta", "metric": "risk", "value": -40}],
    )
    defaults.update(overrides)
    return PromptContext(**defaults)


class TestBuildSystemPrompt:

    def test_returns_persona_for_known_profession(self):
        builder = PromptBuilder()
        prompt = builder.build_system_prompt("software_engineer")
        assert "Alex Rivera" in prompt
        assert "staff engineer" in prompt

    def test_returns_persona_for_doctor(self):
        builder = PromptBuilder()
        prompt = builder.build_system_prompt("doctor")
        assert "Dr. Amara Osei" in prompt

    def test_returns_default_persona_for_unknown(self):
        builder = PromptBuilder()
        prompt = builder.build_system_prompt("unknown_profession")
        assert "mentor" in prompt.lower()

    def test_json_schema_embedded_in_system_prompt(self):
        builder = PromptBuilder()
        prompt = builder.build_system_prompt("software_engineer")
        assert "feedback" in prompt
        assert "key_insight" in prompt
        assert "coaching_question" in prompt
        assert "consequence_analysis" in prompt
        assert "json" in prompt.lower()


class TestBuildUserPrompt:

    def test_includes_step_title_and_narrative(self):
        builder = PromptBuilder()
        ctx = _make_context()
        prompt = builder.build_user_prompt(ctx)
        assert "Production Incident" in prompt
        assert "A critical service is down" in prompt

    def test_includes_chosen_option(self):
        builder = PromptBuilder()
        ctx = _make_context()
        prompt = builder.build_user_prompt(ctx)
        assert "Rollback immediately" in prompt

    def test_includes_other_options_for_alternative_path(self):
        builder = PromptBuilder()
        ctx = _make_context()
        prompt = builder.build_user_prompt(ctx)
        assert "Push a hotfix" in prompt or "Investigate first" in prompt

    def test_includes_metric_impact_when_delta_significant(self):
        builder = PromptBuilder()
        ctx = _make_context()
        prompt = builder.build_user_prompt(ctx)
        assert "Risk" in prompt or "risk" in prompt
        assert "-40" in prompt or "↓" in prompt

    def test_no_metric_impact_when_delta_small(self):
        builder = PromptBuilder()
        ctx = _make_context(
            metrics_before={"risk": 50.0, "reputation": 60.0},
            metrics_after={"risk": 50.3, "reputation": 60.1},
        )
        prompt = builder.build_user_prompt(ctx)
        assert "No significant metric changes" in prompt

    def test_includes_context_data_facts(self):
        builder = PromptBuilder()
        ctx = _make_context()
        prompt = builder.build_user_prompt(ctx)
        assert "severity" in prompt
        assert "P0" in prompt

    def test_includes_rag_docs_when_present(self):
        builder = PromptBuilder()
        ctx = _make_context(retrieved_context=["[Incident Response] Rollback early and often."])
        prompt = builder.build_user_prompt(ctx)
        assert "Relevant Professional Knowledge" in prompt
        assert "Rollback early" in prompt

    def test_no_rag_section_when_empty(self):
        builder = PromptBuilder()
        ctx = _make_context(retrieved_context=[])
        prompt = builder.build_user_prompt(ctx)
        assert "Relevant Professional Knowledge" not in prompt

    def test_includes_session_history(self):
        builder = PromptBuilder()
        history = [
            DecisionHistoryItem(
                step_key="step_0",
                step_title="Team Setup",
                option_key="hire_fast",
                option_label="Hire fast",
                metrics_before={"risk": 50.0, "reputation": 50.0},
                metrics_after={"risk": 55.0, "reputation": 45.0},
            )
        ]
        ctx = _make_context(session_history=history)
        prompt = builder.build_user_prompt(ctx)
        assert "Decision History" in prompt
        assert "Team Setup" in prompt
        assert "Hire fast" in prompt

    def test_shows_trajectory_with_two_or_more_history_items(self):
        builder = PromptBuilder()
        history = [
            DecisionHistoryItem(
                step_key="step_0", step_title="Setup", option_key="a", option_label="Option A",
                metrics_before={"risk": 50.0, "reputation": 50.0},
                metrics_after={"risk": 60.0, "reputation": 40.0},
            ),
            DecisionHistoryItem(
                step_key="step_1", step_title="Crisis", option_key="b", option_label="Option B",
                metrics_before={"risk": 60.0, "reputation": 40.0},
                metrics_after={"risk": 70.0, "reputation": 35.0},
            ),
        ]
        ctx = _make_context(
            session_history=history,
            metrics_before={"risk": 70.0, "reputation": 35.0},
        )
        prompt = builder.build_user_prompt(ctx)
        assert "trajectory" in prompt.lower() or "→" in prompt

    def test_active_state_flags_included(self):
        builder = PromptBuilder()
        ctx = _make_context(state_flags={"incident_declared": True, "escalated": True, "resolved": False})
        prompt = builder.build_user_prompt(ctx)
        assert "incident_declared" in prompt
        assert "escalated" in prompt
        # False flags should not appear
        assert "resolved" not in prompt

    def test_empty_state_flags_produces_no_flags_section(self):
        builder = PromptBuilder()
        ctx = _make_context(state_flags={})
        prompt = builder.build_user_prompt(ctx)
        assert "Active situation flags" not in prompt
