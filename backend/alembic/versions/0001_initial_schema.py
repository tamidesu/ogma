"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── professions ────────────────────────────────────────
    op.create_table(
        "professions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("icon_key", sa.String(50)),
        sa.Column("color_hex", sa.String(7)),
        sa.Column("difficulty_label", sa.String(50)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_professions_slug", "professions", ["slug"])

    # ── scenarios ──────────────────────────────────────────
    op.create_table(
        "scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("profession_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("professions.id"), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("difficulty", sa.SmallInteger, nullable=False),
        sa.Column("estimated_steps", sa.Integer, nullable=False, server_default="5"),
        sa.Column("initial_metrics", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("initial_state", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("tags", postgresql.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_published", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("profession_id", "slug", name="uq_scenario_profession_slug"),
    )
    op.create_index("ix_scenarios_profession_id", "scenarios", ["profession_id"])

    # ── steps ──────────────────────────────────────────────
    op.create_table(
        "steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_key", sa.String(100), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("narrative", sa.Text, nullable=False),
        sa.Column("context_data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("step_type", sa.String(50), nullable=False, server_default="'decision'"),
        sa.Column("is_terminal", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sort_order", sa.Integer, nullable=False),
        sa.UniqueConstraint("scenario_id", "step_key", name="uq_step_scenario_key"),
    )
    op.create_index("ix_steps_scenario_id", "steps", ["scenario_id", "sort_order"])

    # ── decision_options ────────────────────────────────────
    op.create_table(
        "decision_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("step_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("steps.id", ondelete="CASCADE"), nullable=False),
        sa.Column("option_key", sa.String(100), nullable=False),
        sa.Column("label", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("effects", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("preconditions", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("next_step_key", sa.String(100)),
        sa.UniqueConstraint("step_id", "option_key", name="uq_option_step_key"),
    )
    op.create_index("ix_options_step_id", "decision_options", ["step_id"])

    # ── step_transitions ────────────────────────────────────
    op.create_table(
        "step_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_step_key", sa.String(100), nullable=False),
        sa.Column("condition", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("to_step_key", sa.String(100), nullable=False),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
    )

    # ── simulation_sessions ─────────────────────────────────
    op.create_table(
        "simulation_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id"), nullable=False),
        sa.Column("scenario_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(30), nullable=False, server_default="'active'"),
        sa.Column("current_step_key", sa.String(100), nullable=False),
        sa.Column("state_snapshot", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("metrics", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("final_score", sa.Numeric(6, 2)),
        sa.CheckConstraint(
            "status IN ('active', 'paused', 'completed', 'abandoned')",
            name="valid_status",
        ),
    )
    op.create_index("ix_sessions_user_id", "simulation_sessions", ["user_id"])
    op.create_index("ix_sessions_status", "simulation_sessions", ["status"])

    # ── ai_feedback ─────────────────────────────────────────
    op.create_table(
        "ai_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("simulation_sessions.id"), nullable=False),
        sa.Column("step_key", sa.String(100), nullable=False),
        sa.Column("option_key", sa.String(100), nullable=False),
        sa.Column("feedback_text", sa.Text, nullable=False),
        sa.Column("prompt_version", sa.String(20)),
        sa.Column("model_used", sa.String(100)),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("tone", sa.String(50)),
        sa.Column("quality_score", sa.Integer),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_feedback_session_id", "ai_feedback", ["session_id"])

    # ── decision_log ────────────────────────────────────────
    op.create_table(
        "decision_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("simulation_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_key", sa.String(100), nullable=False),
        sa.Column("option_key", sa.String(100), nullable=False),
        sa.Column("effects_applied", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("metrics_before", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("metrics_after", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("state_before", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("state_after", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("ai_feedback_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_feedback.id"), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_spent_sec", sa.Integer),
    )
    op.create_index("ix_decision_log_session_id", "decision_log", ["session_id"])

    # ── skill_profiles ──────────────────────────────────────
    op.create_table(
        "skill_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("xp_total", sa.Integer, nullable=False, server_default="0"),
        sa.Column("level", sa.SmallInteger, nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── skill_scores ────────────────────────────────────────
    op.create_table(
        "skill_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("skill_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skill_profiles.id"), nullable=False),
        sa.Column("profession_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("professions.id"), nullable=False),
        sa.Column("skill_key", sa.String(100), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("skill_profile_id", "profession_id", "skill_key", name="uq_skill_score"),
    )
    op.create_index("ix_skill_scores_profile_id", "skill_scores", ["skill_profile_id"])

    # ── completed_scenarios ─────────────────────────────────
    op.create_table(
        "completed_scenarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("scenario_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenarios.id"), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("simulation_sessions.id"), nullable=False),
        sa.Column("skill_profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skill_profiles.id"), nullable=False),
        sa.Column("final_score", sa.Numeric(6, 2), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_completed_scenarios_user_id", "completed_scenarios", ["user_id"])


def downgrade() -> None:
    op.drop_table("completed_scenarios")
    op.drop_table("skill_scores")
    op.drop_table("skill_profiles")
    op.drop_table("decision_log")
    op.drop_table("simulation_sessions")
    op.drop_table("ai_feedback")
    op.drop_table("step_transitions")
    op.drop_table("decision_options")
    op.drop_table("steps")
    op.drop_table("scenarios")
    op.drop_table("professions")
    op.drop_table("users")
