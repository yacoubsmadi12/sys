from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BlockedUserBase(BaseModel):
    pattern: str = Field(..., min_length=1, max_length=256, description="Username or regex pattern")


class BlockedUserCreate(BlockedUserBase):
    pass


class BlockedUserRead(BlockedUserBase):
    id: str
    filter_rule_id: str
    source_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class FilterRuleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    source_id: str
    description: Optional[str] = None
    field: str = Field("username", description="username / hostname / message")
    pattern_type: str = Field("exact", description="exact / regex / contains")
    action: str = Field("drop", description="Currently only 'drop' is supported")
    enabled: bool = True


class FilterRuleCreate(FilterRuleBase):
    patterns: list[str] = Field(default_factory=list, description="Initial list of patterns/usernames to block")


class FilterRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    field: Optional[str] = None
    pattern_type: Optional[str] = None
    enabled: Optional[bool] = None


class FilterRuleRead(FilterRuleBase):
    id: str
    blocked_users: list[BlockedUserRead] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FilterRuleList(BaseModel):
    items: list[FilterRuleRead]
    total: int
