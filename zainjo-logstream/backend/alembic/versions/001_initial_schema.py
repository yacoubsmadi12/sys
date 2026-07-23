"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "log_sources",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("vendor", sa.String(64), nullable=False),
        sa.Column("system_type", sa.String(64), nullable=False),
        sa.Column("protocol", sa.String(8), nullable=False, server_default="UDP"),
        sa.Column("port", sa.Integer, nullable=False, server_default="1514"),
        sa.Column("description", sa.String(512)),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_log_sources_name", "log_sources", ["name"])
    op.create_index("ix_log_sources_ip_address", "log_sources", ["ip_address"])

    op.create_table(
        "filter_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("log_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.String(512)),
        sa.Column("field", sa.String(64), nullable=False, server_default="username"),
        sa.Column("pattern_type", sa.String(16), nullable=False, server_default="exact"),
        sa.Column("action", sa.String(16), nullable=False, server_default="drop"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_filter_rules_source_id", "filter_rules", ["source_id"])

    op.create_table(
        "blocked_users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("filter_rule_id", sa.String(36), sa.ForeignKey("filter_rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", sa.String(36), sa.ForeignKey("log_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pattern", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_blocked_users_filter_rule_id", "blocked_users", ["filter_rule_id"])
    op.create_index("ix_blocked_users_source_id", "blocked_users", ["source_id"])

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(256), nullable=False),
        sa.Column("full_name", sa.String(128)),
        sa.Column("email", sa.String(256)),
        sa.Column("role", sa.String(16), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("last_login", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "syslog_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("log_timestamp", sa.DateTime(timezone=True)),
        sa.Column("source_ip", sa.String(45), nullable=False),
        sa.Column("source_id", sa.String(36)),
        sa.Column("source_name", sa.String(128)),
        sa.Column("vendor", sa.String(64)),
        sa.Column("hostname", sa.String(256)),
        sa.Column("app_name", sa.String(128)),
        sa.Column("proc_id", sa.String(64)),
        sa.Column("msg_id", sa.String(64)),
        sa.Column("facility", sa.Integer),
        sa.Column("severity", sa.Integer),
        sa.Column("severity_name", sa.String(16)),
        sa.Column("raw_message", sa.Text, nullable=False),
        sa.Column("message", sa.Text),
        sa.Column("parsed_fields", sa.JSON),
        sa.Column("username", sa.String(128)),
        sa.Column("is_dropped", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("drop_reason", sa.String(256)),
        sa.Column("forwarded_to_siem", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("processed", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_index("ix_syslog_entries_received_at", "syslog_entries", ["received_at"])
    op.create_index("ix_syslog_entries_source_ip", "syslog_entries", ["source_ip"])
    op.create_index("ix_syslog_entries_source_name", "syslog_entries", ["source_name"])
    op.create_index("ix_syslog_entries_vendor", "syslog_entries", ["vendor"])
    op.create_index("ix_syslog_entries_username", "syslog_entries", ["username"])
    op.create_index("ix_syslog_entries_is_dropped", "syslog_entries", ["is_dropped"])
    op.create_index("ix_syslog_entries_source_vendor", "syslog_entries", ["source_name", "vendor"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("source_ip", sa.String(45), nullable=False),
        sa.Column("source_name", sa.String(128)),
        sa.Column("vendor", sa.String(64)),
        sa.Column("username", sa.String(128)),
        sa.Column("raw_message", sa.Text, nullable=False),
        sa.Column("action", sa.String(16), nullable=False, server_default="drop"),
        sa.Column("reason", sa.String(256), nullable=False),
        sa.Column("rule_id", sa.String(36)),
        sa.Column("rule_name", sa.String(128)),
        sa.Column("matched_pattern", sa.String(256)),
    )
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])
    op.create_index("ix_audit_logs_source_ip", "audit_logs", ["source_ip"])
    op.create_index("ix_audit_logs_source_name", "audit_logs", ["source_name"])
    op.create_index("ix_audit_logs_username", "audit_logs", ["username"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("syslog_entries")
    op.drop_table("users")
    op.drop_table("blocked_users")
    op.drop_table("filter_rules")
    op.drop_table("log_sources")
