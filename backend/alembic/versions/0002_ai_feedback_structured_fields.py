"""add structured fields to ai_feedback

Revision ID: 0002
Revises: 0001
Create Date: 2024-01-02 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ai_feedback", sa.Column("key_insight", sa.Text, nullable=True))
    op.add_column("ai_feedback", sa.Column("coaching_question", sa.Text, nullable=True))
    op.add_column("ai_feedback", sa.Column("consequence_analysis", sa.Text, nullable=True))
    op.add_column("ai_feedback", sa.Column("alternative_path", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("ai_feedback", "alternative_path")
    op.drop_column("ai_feedback", "consequence_analysis")
    op.drop_column("ai_feedback", "coaching_question")
    op.drop_column("ai_feedback", "key_insight")
