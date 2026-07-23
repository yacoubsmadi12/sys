"""
SyslogEntry model — stores a received syslog message.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, Text, JSON, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class SyslogEntry(Base):
    __tablename__ = "syslog_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Timing
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    log_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    # Network origin
    source_ip: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    source_id: Mapped[str | None] = mapped_column(String(36), index=True)   # FK to log_sources (no hard FK for perf)
    source_name: Mapped[str | None] = mapped_column(String(128), index=True)
    vendor: Mapped[str | None] = mapped_column(String(64), index=True)       # Huawei / Nokia / Ericsson

    # Syslog header fields
    hostname: Mapped[str | None] = mapped_column(String(256), index=True)
    app_name: Mapped[str | None] = mapped_column(String(128), index=True)
    proc_id: Mapped[str | None] = mapped_column(String(64))
    msg_id: Mapped[str | None] = mapped_column(String(64))
    facility: Mapped[int | None] = mapped_column(Integer)
    severity: Mapped[int | None] = mapped_column(Integer, index=True)
    severity_name: Mapped[str | None] = mapped_column(String(16), index=True)

    # Message
    raw_message: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str | None] = mapped_column(Text)

    # Parsed vendor fields (JSON blob)
    parsed_fields: Mapped[dict | None] = mapped_column(JSON)

    # Extracted username (for filtering and search)
    username: Mapped[str | None] = mapped_column(String(128), index=True)

    # Processing state
    is_dropped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    drop_reason: Mapped[str | None] = mapped_column(String(256))
    forwarded_to_siem: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_syslog_entries_source_vendor", "source_name", "vendor"),
        Index("ix_syslog_entries_received_dropped", "received_at", "is_dropped"),
        Index("ix_syslog_entries_username_source", "username", "source_name"),
    )
