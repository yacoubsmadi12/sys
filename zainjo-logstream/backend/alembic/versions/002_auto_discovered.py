"""Add auto_discovered column to log_sources

Revision ID: 002
Revises: 001
Create Date: 2026-07-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "log_sources",
        sa.Column("auto_discovered", sa.Boolean, nullable=False, server_default="false"),
    )
    op.add_column(
        "log_sources",
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "log_sources",
        sa.Column("log_count", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("log_sources", "log_count")
    op.drop_column("log_sources", "last_seen_at")
    op.drop_column("log_sources", "auto_discovered")
