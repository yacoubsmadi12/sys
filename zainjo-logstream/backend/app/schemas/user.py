from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: str = Field("viewer", description="admin / viewer")
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserRead(UserBase):
    id: str
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserList(BaseModel):
    items: list[UserRead]
    total: int
