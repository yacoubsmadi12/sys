"""
Log search and retrieval endpoints.
"""
import math
import shutil
from pathlib import Path
from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, func, and_, or_, desc

from app.api.deps import get_current_user, require_admin, get_db
from app.config import settings
from app.models.audit import AuditLog
from app.models.user import User
from app.models.log import SyslogEntry
from app.schemas.log import SyslogEntryRead, SyslogEntryList

router = APIRouter(prefix="/logs", tags=["Logs"])


def _clear_storage_logs() -> None:
    """Remove stored log files while preserving the configured root directory."""
    root = Path(settings.storage_path)
    if not root.exists():
        return

    # These directories are created by the collector and contain log data or
    # failed/processed log payloads. Keep the root and recreate the folders so
    # the running workers can continue writing without a restart.
    for name in ("raw", "archive", "processed", "failed"):
        child = root / name
        if child.exists():
            shutil.rmtree(child)
        child.mkdir(parents=True, exist_ok=True)


@router.delete("/all", status_code=200)
async def delete_all_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> dict[str, int | str]:
    """Delete every stored log and its drop-audit record."""
    log_result = await db.execute(delete(SyslogEntry))
    audit_result = await db.execute(delete(AuditLog))
    await db.commit()
    _clear_storage_logs()
    return {
        "status": "ok",
        "deleted_logs": log_result.rowcount or 0,
        "deleted_audit_logs": audit_result.rowcount or 0,
    }


@router.get("", response_model=SyslogEntryList)
async def search_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    username: Optional[str] = Query(None),
    source_name: Optional[str] = Query(None),
    vendor: Optional[str] = Query(None),
    source_ip: Optional[str] = Query(None),
    severity_name: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    is_dropped: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
) -> SyslogEntryList:

    conditions = []
    if username:
        conditions.append(SyslogEntry.username.ilike(f"%{username}%"))
    if source_name:
        conditions.append(SyslogEntry.source_name.ilike(f"%{source_name}%"))
    if vendor:
        conditions.append(SyslogEntry.vendor.ilike(f"%{vendor}%"))
    if source_ip:
        conditions.append(SyslogEntry.source_ip.ilike(f"%{source_ip}%"))
    if severity_name:
        conditions.append(SyslogEntry.severity_name.ilike(f"%{severity_name}%"))
    if keyword:
        conditions.append(
            or_(
                SyslogEntry.raw_message.ilike(f"%{keyword}%"),
                SyslogEntry.message.ilike(f"%{keyword}%"),
            )
        )
    if from_date:
        conditions.append(SyslogEntry.received_at >= from_date)
    if to_date:
        conditions.append(SyslogEntry.received_at <= to_date)
    if is_dropped is not None:
        conditions.append(SyslogEntry.is_dropped == is_dropped)

    where_clause = and_(*conditions) if conditions else True

    total_result = await db.execute(
        select(func.count()).select_from(SyslogEntry).where(where_clause)
    )
    total = total_result.scalar_one() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        select(SyslogEntry)
        .where(where_clause)
        .order_by(desc(SyslogEntry.received_at))
        .offset(offset)
        .limit(page_size)
    )
    entries = result.scalars().all()

    return SyslogEntryList(
        items=[SyslogEntryRead.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/{log_id}", response_model=SyslogEntryRead)
async def get_log(
    log_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> SyslogEntryRead:
    from fastapi import HTTPException
    result = await db.execute(select(SyslogEntry).where(SyslogEntry.id == log_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return SyslogEntryRead.model_validate(entry)
