"""Add rule_id, rule_name, matched_pattern to syslog_entries

These columns exist in the ORM model but were absent from the initial
production schema (migration 001 was applied before they were added).

Revision ID: 004
Revises: 003
Create Date: 2026-07-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use IF NOT EXISTS logic via a DO block so this is safe to run even
    # on environments where migration 001 already included these columns.
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'syslog_entries' AND column_name = 'rule_id'
            ) THEN
                ALTER TABLE syslog_entries ADD COLUMN rule_id VARCHAR(36);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'syslog_entries' AND column_name = 'rule_name'
            ) THEN
                ALTER TABLE syslog_entries ADD COLUMN rule_name VARCHAR(128);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'syslog_entries' AND column_name = 'matched_pattern'
            ) THEN
                ALTER TABLE syslog_entries ADD COLUMN matched_pattern VARCHAR(256);
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.drop_column("syslog_entries", "matched_pattern")
    op.drop_column("syslog_entries", "rule_name")
    op.drop_column("syslog_entries", "rule_id")
