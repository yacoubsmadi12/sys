"""
Dashboard statistics endpoint.
"""
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.log import SyslogEntry
from app.models.source import LogSource
from app.models.filter import FilterRule
from app.schemas.dashboard import (
    DashboardStats, CountByVendor, CountBySource, TopUser, RecentEvent
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> DashboardStats:

    # Total counts
    total_result = await db.execute(select(func.count()).select_from(SyslogEntry))
    total = total_result.scalar_one() or 0

    dropped_result = await db.execute(
        select(func.count()).select_from(SyslogEntry).where(SyslogEntry.is_dropped == True)
    )
    dropped = dropped_result.scalar_one() or 0

    forwarded_result = await db.execute(
        select(func.count()).select_from(SyslogEntry).where(SyslogEntry.forwarded_to_siem == True)
    )
    forwarded = forwarded_result.scalar_one() or 0

    accepted = total - dropped

    # Logs by vendor
    vendor_result = await db.execute(
        select(SyslogEntry.vendor, func.count().label("count"))
        .where(SyslogEntry.vendor.isnot(None))
        .group_by(SyslogEntry.vendor)
        .order_by(desc("count"))
        .limit(10)
    )
    logs_by_vendor = [CountByVendor(vendor=row.vendor, count=row.count) for row in vendor_result]

    # Logs by source (top 10)
    source_result = await db.execute(
        select(SyslogEntry.source_name, func.count().label("count"))
        .where(SyslogEntry.source_name.isnot(None))
        .group_by(SyslogEntry.source_name)
        .order_by(desc("count"))
        .limit(10)
    )
    logs_by_source = [
        CountBySource(source_name=row.source_name, count=row.count)
        for row in source_result
    ]

    # Top users (by username, accepted only)
    user_result = await db.execute(
        select(SyslogEntry.username, func.count().label("count"))
        .where(SyslogEntry.username.isnot(None), SyslogEntry.is_dropped == False)
        .group_by(SyslogEntry.username)
        .order_by(desc("count"))
        .limit(10)
    )
    top_users = [TopUser(username=row.username, count=row.count) for row in user_result]

    # Recent events (last 20)
    recent_result = await db.execute(
        select(SyslogEntry)
        .order_by(desc(SyslogEntry.received_at))
        .limit(20)
    )
    recent_entries = recent_result.scalars().all()
    recent_events = [
        RecentEvent(
            id=e.id,
            received_at=e.received_at,
            source_name=e.source_name,
            vendor=e.vendor,
            severity_name=e.severity_name,
            username=e.username,
            message=e.message[:200] if e.message else e.raw_message[:200],
            is_dropped=e.is_dropped,
        )
        for e in recent_entries
    ]

    # Source counts
    src_total = await db.execute(select(func.count()).select_from(LogSource))
    src_active = await db.execute(
        select(func.count()).select_from(LogSource).where(LogSource.enabled == True)
    )
    filter_active = await db.execute(
        select(func.count()).select_from(FilterRule).where(FilterRule.enabled == True)
    )

    return DashboardStats(
        total_received=total,
        total_accepted=accepted,
        total_dropped=dropped,
        total_forwarded=forwarded,
        logs_by_vendor=logs_by_vendor,
        logs_by_source=logs_by_source,
        top_users=top_users,
        recent_events=recent_events,
        active_sources=src_active.scalar_one() or 0,
        total_sources=src_total.scalar_one() or 0,
        active_filter_rules=filter_active.scalar_one() or 0,
    )
