from datetime import datetime
from typing import Any
from pydantic import BaseModel


class CountByVendor(BaseModel):
    vendor: str
    count: int


class CountBySource(BaseModel):
    source_name: str
    count: int


class TopUser(BaseModel):
    username: str
    count: int


class RecentEvent(BaseModel):
    id: str
    received_at: datetime
    source_name: str | None
    vendor: str | None
    severity_name: str | None
    username: str | None
    message: str | None
    is_dropped: bool


class DashboardStats(BaseModel):
    total_received: int
    total_accepted: int
    total_dropped: int
    total_forwarded: int
    logs_by_vendor: list[CountByVendor]
    logs_by_source: list[CountBySource]
    top_users: list[TopUser]
    recent_events: list[RecentEvent]
    active_sources: int
    total_sources: int
    active_filter_rules: int


class AuditLogRead(BaseModel):
    id: str
    timestamp: datetime
    source_ip: str
    source_name: str | None
    vendor: str | None
    username: str | None
    raw_message: str
    action: str
    reason: str
    rule_id: str | None
    rule_name: str | None
    matched_pattern: str | None

    class Config:
        from_attributes = True


class AuditLogList(BaseModel):
    items: list[AuditLogRead]
    total: int
    page: int
    page_size: int
    pages: int
