"""
FilterRule and BlockedUser models.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class FilterRule(Base):
    __tablename__ = "filter_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("log_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(512))
    field: Mapped[str] = mapped_column(String(64), nullable=False, default="username")  # username / hostname / message
    pattern_type: Mapped[str] = mapped_column(String(16), nullable=False, default="exact")  # exact / regex / contains
    action: Mapped[str] = mapped_column(String(16), nullable=False, default="drop")  # drop only for now
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    source: Mapped["LogSource"] = relationship("LogSource", back_populates="filter_rules")
    blocked_users: Mapped[list["BlockedUser"]] = relationship(
        "BlockedUser", back_populates="filter_rule", cascade="all, delete-orphan", lazy="select"
    )


class BlockedUser(Base):
    __tablename__ = "blocked_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filter_rule_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("filter_rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("log_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pattern: Mapped[str] = mapped_column(String(256), nullable=False)  # username or regex pattern
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    filter_rule: Mapped["FilterRule"] = relationship("FilterRule", back_populates="blocked_users")
