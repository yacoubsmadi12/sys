from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


class SyslogEntryRead(BaseModel):
    id: str
    received_at: datetime
    log_timestamp: Optional[datetime] = None
    source_ip: str
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    vendor: Optional[str] = None
    hostname: Optional[str] = None
    app_name: Optional[str] = None
    facility: Optional[int] = None
    severity: Optional[int] = None
    severity_name: Optional[str] = None
    raw_message: str
    message: Optional[str] = None
    parsed_fields: Optional[dict[str, Any]] = None
    username: Optional[str] = None
    is_dropped: bool
    drop_reason: Optional[str] = None
    forwarded_to_siem: bool
    processed: bool

    class Config:
        from_attributes = True


class SyslogSearchParams(BaseModel):
    username: Optional[str] = None
    source_name: Optional[str] = None
    vendor: Optional[str] = None
    source_ip: Optional[str] = None
    severity_name: Optional[str] = None
    keyword: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    is_dropped: Optional[bool] = None
    page: int = 1
    page_size: int = 50


class SyslogEntryList(BaseModel):
    items: list[SyslogEntryRead]
    total: int
    page: int
    page_size: int
    pages: int
