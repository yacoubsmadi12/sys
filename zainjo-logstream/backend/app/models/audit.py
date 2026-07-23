"""
AuditLog model — records every dropped log event with the matching rule.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Origin
    source_ip: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    source_name: Mapped[str | None] = mapped_column(String(128), index=True)
    vendor: Mapped[str | None] = mapped_column(String(64))

    # What was in the log
    username: Mapped[str | None] = mapped_column(String(128), index=True)
    raw_message: Mapped[str] = mapped_column(Text, nullable=False)

    # Why it was dropped
    action: Mapped[str] = mapped_column(String(16), nullable=False, default="drop")
    reason: Mapped[str] = mapped_column(String(256), nullable=False)
    rule_id: Mapped[str | None] = mapped_column(String(36))
    rule_name: Mapped[str | None] = mapped_column(String(128))
    matched_pattern: Mapped[str | None] = mapped_column(String(256))

    __table_args__ = (
        Index("ix_audit_logs_source_timestamp", "source_name", "timestamp"),
    )
