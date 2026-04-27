"""open-world simulation: briefs, agent turns, world snapshots, npc state, image assets

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-27 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── scenario_briefs ────────────────────────────────────────────────
    op.create_table(
        "scenario_briefs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("profession_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("professions.id"), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("case_file_md", sa.Text, nullable=False),
        sa.Column("initial_world_state", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("success_criteria_jsonlogic", postgresql.JSONB, nullable=True),
        sa.Column("failure_criteria_jsonlogic", postgresql.JSONB, nullable=True),
        sa.Column("timeout_resolution", sa.Text, nullable=True),
        sa.Column("max_turns", sa.Integer, nullable=False, server_default="12"),
        sa.Column("npc_definition", postgresql.JSONB, nullable=False),
        sa.Column("complication_pool", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("knowledge_tags", postgresql.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("initial_suggested_actions", postgresql.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("difficulty", sa.Integer, nullable=False, server_default="3"),
        sa.Column("estimated_turns", sa.Integer, nullable=False, server_default="6"),
        sa.Column("locale", sa.String(10), nullable=False, server_default="'kk'"),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("profession_id", "slug", name="uq_brief_profession_slug"),
    )
    op.create_index("ix_scenario_briefs_profession_id", "scenario_briefs", ["profession_id"])

    # ── simulation_sessions: add mode + brief_id (nullable for backward compat) ──
    op.add_column(
        "simulation_sessions",
        sa.Column("mode", sa.String(20), nullable=False, server_default="'guided'"),
    )
    op.add_column(
        "simulation_sessions",
        sa.Column("brief_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("scenario_briefs.id"), nullable=True),
    )
    op.create_index("ix_simulation_sessions_brief_id", "simulation_sessions", ["brief_id"])
    op.create_check_constraint(
        "valid_mode",
        "simulation_sessions",
        "mode IN ('guided', 'open_world')",
    )

    # ── agent_turns ────────────────────────────────────────────────────
    op.create_table(
        "agent_turns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("simulation_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("turn_index", sa.Integer, nullable=False),
        sa.Column("user_input", sa.Text, nullable=False),
        sa.Column("locale", sa.String(10), nullable=False, server_default="'kk'"),
        sa.Column("intent_json", postgresql.JSONB, nullable=False),
        sa.Column("validation_json", postgresql.JSONB, nullable=False),
        sa.Column("npc_update_json", postgresql.JSONB, nullable=False),
        sa.Column("world_delta_json", postgresql.JSONB, nullable=False),
        sa.Column("image_id", sa.String(200), nullable=True),
        sa.Column("mentor_feedback_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("ai_feedback.id"), nullable=True),
        sa.Column("is_terminal", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("termination_reason", sa.String(50), nullable=True),
        sa.Column("pipeline_latency_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("session_id", "turn_index", name="uq_turn_session_index"),
    )
    op.create_index("ix_agent_turns_session_id", "agent_turns", ["session_id"])

    # ── world_state_snapshots ──────────────────────────────────────────
    op.create_table(
        "world_state_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("simulation_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("turn_index", sa.Integer, nullable=False),
        sa.Column("state_json", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("session_id", "turn_index", name="uq_world_session_turn"),
    )
    op.create_index("ix_world_state_snapshots_session_id", "world_state_snapshots", ["session_id"])

    # ── npc_states (one row per active session) ────────────────────────
    op.create_table(
        "npc_states",
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("simulation_sessions.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("definition_id", sa.String(100), nullable=False),
        sa.Column("emotion_json", postgresql.JSONB, nullable=False),
        sa.Column("relationship_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("memory_json", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("current_label", sa.String(80), nullable=True),
        sa.Column("current_avatar_id", sa.String(200), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── image_assets (mirror of manifest.json) ─────────────────────────
    op.create_table(
        "image_assets",
        sa.Column("id", sa.String(200), primary_key=True),
        sa.Column("file_path", sa.String(400), nullable=False),
        sa.Column("profession_slug", sa.String(100), nullable=False),
        sa.Column("scene_category", sa.String(80), nullable=False),
        sa.Column("mood", sa.String(40), nullable=False),
        sa.Column("characters_present", postgresql.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("world_flags_match", postgresql.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("tags", postgresql.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_image_assets_profession_slug", "image_assets", ["profession_slug"])
    op.create_index("ix_image_assets_scene_category", "image_assets", ["scene_category"])


def downgrade() -> None:
    op.drop_index("ix_image_assets_scene_category", table_name="image_assets")
    op.drop_index("ix_image_assets_profession_slug", table_name="image_assets")
    op.drop_table("image_assets")

    op.drop_table("npc_states")

    op.drop_index("ix_world_state_snapshots_session_id", table_name="world_state_snapshots")
    op.drop_table("world_state_snapshots")

    op.drop_index("ix_agent_turns_session_id", table_name="agent_turns")
    op.drop_table("agent_turns")

    op.drop_constraint("valid_mode", "simulation_sessions", type_="check")
    op.drop_index("ix_simulation_sessions_brief_id", table_name="simulation_sessions")
    op.drop_column("simulation_sessions", "brief_id")
    op.drop_column("simulation_sessions", "mode")

    op.drop_index("ix_scenario_briefs_profession_id", table_name="scenario_briefs")
    op.drop_table("scenario_briefs")
