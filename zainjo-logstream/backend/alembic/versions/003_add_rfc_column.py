"""Add rfc column to syslog_entries

Revision ID: 003
Revises: 002
Create Date: 2026-07-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "syslog_entries",
        sa.Column("rfc", sa.String(8), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("syslog_entries", "rfc")
