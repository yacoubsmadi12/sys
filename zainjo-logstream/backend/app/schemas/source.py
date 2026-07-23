from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, IPvAnyAddress


class LogSourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    ip_address: str = Field(..., description="Source IP address")
    vendor: str = Field(..., description="Huawei / Nokia / Ericsson")
    system_type: str = Field(..., description="NCE / U2020 / NetAct / ENM / etc.")
    protocol: str = Field("UDP", description="UDP / TCP / BOTH")
    port: int = Field(1514, ge=1, le=65535)
    description: Optional[str] = None
    enabled: bool = True


class LogSourceCreate(LogSourceBase):
    pass


class LogSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    ip_address: Optional[str] = None
    vendor: Optional[str] = None
    system_type: Optional[str] = None
    protocol: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535)
    description: Optional[str] = None
    enabled: Optional[bool] = None


class LogSourceRead(LogSourceBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LogSourceList(BaseModel):
    items: list[LogSourceRead]
    total: int
