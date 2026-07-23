-- ZainJo LogStream – PostgreSQL schema
-- Run: psql -U logstream -d logstream -f schema.sql
--
-- If you use Alembic migrations (recommended), run:
--   cd backend && alembic upgrade head
-- instead of executing this file directly.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Sources
CREATE TABLE IF NOT EXISTS log_sources (
    id           VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    name         VARCHAR(128) NOT NULL UNIQUE,
    ip_address   VARCHAR(45)  NOT NULL,
    vendor       VARCHAR(64)  NOT NULL,
    system_type  VARCHAR(64)  NOT NULL,
    protocol     VARCHAR(8)   NOT NULL DEFAULT 'UDP',
    port         INTEGER      NOT NULL DEFAULT 1514,
    description  VARCHAR(512),
    enabled      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_log_sources_name       ON log_sources(name);
CREATE INDEX IF NOT EXISTS ix_log_sources_ip_address ON log_sources(ip_address);

-- Filter rules
CREATE TABLE IF NOT EXISTS filter_rules (
    id           VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    source_id    VARCHAR(36)  NOT NULL REFERENCES log_sources(id) ON DELETE CASCADE,
    name         VARCHAR(128) NOT NULL,
    description  VARCHAR(512),
    field        VARCHAR(64)  NOT NULL DEFAULT 'username',
    pattern_type VARCHAR(16)  NOT NULL DEFAULT 'exact',
    action       VARCHAR(16)  NOT NULL DEFAULT 'drop',
    enabled      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_filter_rules_source_id ON filter_rules(source_id);

-- Blocked user patterns
CREATE TABLE IF NOT EXISTS blocked_users (
    id              VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    filter_rule_id  VARCHAR(36)  NOT NULL REFERENCES filter_rules(id) ON DELETE CASCADE,
    source_id       VARCHAR(36)  NOT NULL REFERENCES log_sources(id) ON DELETE CASCADE,
    pattern         VARCHAR(256) NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_blocked_users_filter_rule_id ON blocked_users(filter_rule_id);
CREATE INDEX IF NOT EXISTS ix_blocked_users_source_id      ON blocked_users(source_id);

-- Application users
CREATE TABLE IF NOT EXISTS users (
    id              VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    username        VARCHAR(64)  NOT NULL UNIQUE,
    hashed_password VARCHAR(256) NOT NULL,
    full_name       VARCHAR(128),
    email           VARCHAR(256),
    role            VARCHAR(16)  NOT NULL DEFAULT 'viewer',
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    last_login      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);

-- Syslog entries
CREATE TABLE IF NOT EXISTS syslog_entries (
    id                 VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    received_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    log_timestamp      TIMESTAMPTZ,
    source_ip          VARCHAR(45)  NOT NULL,
    source_id          VARCHAR(36),
    source_name        VARCHAR(128),
    vendor             VARCHAR(64),
    hostname           VARCHAR(256),
    app_name           VARCHAR(128),
    proc_id            VARCHAR(64),
    msg_id             VARCHAR(64),
    facility           INTEGER,
    severity           INTEGER,
    severity_name      VARCHAR(16),
    raw_message        TEXT         NOT NULL,
    message            TEXT,
    parsed_fields      JSONB,
    username           VARCHAR(128),
    is_dropped         BOOLEAN      NOT NULL DEFAULT FALSE,
    drop_reason        VARCHAR(256),
    forwarded_to_siem  BOOLEAN      NOT NULL DEFAULT FALSE,
    processed          BOOLEAN      NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_syslog_entries_received_at     ON syslog_entries(received_at DESC);
CREATE INDEX IF NOT EXISTS ix_syslog_entries_source_ip       ON syslog_entries(source_ip);
CREATE INDEX IF NOT EXISTS ix_syslog_entries_source_name     ON syslog_entries(source_name);
CREATE INDEX IF NOT EXISTS ix_syslog_entries_vendor          ON syslog_entries(vendor);
CREATE INDEX IF NOT EXISTS ix_syslog_entries_username        ON syslog_entries(username);
CREATE INDEX IF NOT EXISTS ix_syslog_entries_is_dropped      ON syslog_entries(is_dropped);
CREATE INDEX IF NOT EXISTS ix_syslog_entries_received_dropped ON syslog_entries(received_at DESC, is_dropped);

-- Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id              VARCHAR(36)  PRIMARY KEY DEFAULT gen_random_uuid()::TEXT,
    timestamp       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    source_ip       VARCHAR(45)  NOT NULL,
    source_name     VARCHAR(128),
    vendor          VARCHAR(64),
    username        VARCHAR(128),
    raw_message     TEXT         NOT NULL,
    action          VARCHAR(16)  NOT NULL DEFAULT 'drop',
    reason          VARCHAR(256) NOT NULL,
    rule_id         VARCHAR(36),
    rule_name       VARCHAR(128),
    matched_pattern VARCHAR(256)
);
CREATE INDEX IF NOT EXISTS ix_audit_logs_timestamp   ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_audit_logs_source_name ON audit_logs(source_name);
CREATE INDEX IF NOT EXISTS ix_audit_logs_username    ON audit_logs(username);
