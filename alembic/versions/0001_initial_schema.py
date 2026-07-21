"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("prompt_version", sa.String(length=50), nullable=False),
        sa.Column("raw_response", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_runs_created_at", "analysis_runs", ["created_at"], unique=False)
    op.create_index("ix_analysis_runs_executed_at", "analysis_runs", ["executed_at"], unique=False)

    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("title", "published_at", name="uq_signals_title_published_at"),
    )
    op.create_index("ix_signals_content_hash", "signals", ["content_hash"], unique=False)
    op.create_index("ix_signals_created_at", "signals", ["created_at"], unique=False)
    op.create_index("ix_signals_published_at", "signals", ["published_at"], unique=False)
    op.create_index("ix_signals_source", "signals", ["source"], unique=False)
    op.create_index("ix_signals_unique_url", "signals", ["url"], unique=True, postgresql_where=sa.text("url IS NOT NULL"))

    op.create_table(
        "topic_summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("analysis_run_id", sa.Integer(), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("score", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("video_ideas", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_topic_summaries_analysis_run_id", "topic_summaries", ["analysis_run_id"], unique=False)
    op.create_index("ix_topic_summaries_created_at", "topic_summaries", ["created_at"], unique=False)
    op.create_index("ix_topic_summaries_topic", "topic_summaries", ["topic"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_topic_summaries_topic", table_name="topic_summaries")
    op.drop_index("ix_topic_summaries_created_at", table_name="topic_summaries")
    op.drop_index("ix_topic_summaries_analysis_run_id", table_name="topic_summaries")
    op.drop_table("topic_summaries")

    op.drop_index("ix_signals_unique_url", table_name="signals")
    op.drop_index("ix_signals_source", table_name="signals")
    op.drop_index("ix_signals_published_at", table_name="signals")
    op.drop_index("ix_signals_created_at", table_name="signals")
    op.drop_index("ix_signals_content_hash", table_name="signals")
    op.drop_table("signals")

    op.drop_index("ix_analysis_runs_executed_at", table_name="analysis_runs")
    op.drop_index("ix_analysis_runs_created_at", table_name="analysis_runs")
    op.drop_table("analysis_runs")
