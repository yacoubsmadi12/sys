"""
Audit log endpoints — view dropped log events.
"""
import math
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.dashboard import AuditLogRead, AuditLogList

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=AuditLogList)
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    source_name: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    vendor: Optional[str] = Query(None),
    rule_name: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> AuditLogList:

    conditions = []
    if source_name:
        conditions.append(AuditLog.source_name.ilike(f"%{source_name}%"))
    if username:
        conditions.append(AuditLog.username.ilike(f"%{username}%"))
    if vendor:
        conditions.append(AuditLog.vendor.ilike(f"%{vendor}%"))
    if rule_name:
        conditions.append(AuditLog.rule_name.ilike(f"%{rule_name}%"))
    if from_date:
        conditions.append(AuditLog.timestamp >= from_date)
    if to_date:
        conditions.append(AuditLog.timestamp <= to_date)

    where_clause = and_(*conditions) if conditions else True

    total = (
        await db.execute(select(func.count()).select_from(AuditLog).where(where_clause))
    ).scalar_one() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(AuditLog)
        .where(where_clause)
        .order_by(desc(AuditLog.timestamp))
        .offset(offset)
        .limit(page_size)
    )
    entries = result.scalars().all()

    return AuditLogList(
        items=[AuditLogRead.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )
