"""
LogSource model — represents a network device that sends syslog messages.
"""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class LogSource(Base):
    __tablename__ = "log_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    vendor: Mapped[str] = mapped_column(String(64), nullable=False)   # Huawei / Nokia / Ericsson
    system_type: Mapped[str] = mapped_column(String(64), nullable=False)  # NCE / U2020 / NetAct / ENM
    protocol: Mapped[str] = mapped_column(String(8), nullable=False, default="UDP")  # UDP / TCP / BOTH
    port: Mapped[int] = mapped_column(Integer, nullable=False, default=1514)
    description: Mapped[str | None] = mapped_column(String(512))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    filter_rules: Mapped[list["FilterRule"]] = relationship(
        "FilterRule", back_populates="source", cascade="all, delete-orphan", lazy="select"
    )
