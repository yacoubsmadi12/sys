"""
Source management CRUD endpoints.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_current_user, require_admin, get_db
from app.models.user import User
from app.models.source import LogSource
from app.schemas.source import LogSourceCreate, LogSourceRead, LogSourceUpdate, LogSourceList

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("", response_model=LogSourceList)
async def list_sources(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    page: int = 1,
    page_size: int = 100,
) -> LogSourceList:
    total_result = await db.execute(select(func.count()).select_from(LogSource))
    total = total_result.scalar_one() or 0
    offset = (page - 1) * page_size
    result = await db.execute(
        select(LogSource).order_by(LogSource.name).offset(offset).limit(page_size)
    )
    sources = result.scalars().all()
    return LogSourceList(items=[LogSourceRead.model_validate(s) for s in sources], total=total)


@router.get("/{source_id}", response_model=LogSourceRead)
async def get_source(
    source_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> LogSourceRead:
    result = await db.execute(select(LogSource).where(LogSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return LogSourceRead.model_validate(source)


@router.post("", response_model=LogSourceRead, status_code=201)
async def create_source(
    body: LogSourceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> LogSourceRead:
    # Check uniqueness
    result = await db.execute(
        select(LogSource).where(
            (LogSource.name == body.name) | (LogSource.ip_address == body.ip_address)
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Source with this name or IP already exists")
    source = LogSource(**body.model_dump())
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return LogSourceRead.model_validate(source)


@router.patch("/{source_id}", response_model=LogSourceRead)
async def update_source(
    source_id: str,
    body: LogSourceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> LogSourceRead:
    result = await db.execute(select(LogSource).where(LogSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(source, field, value)
    await db.commit()
    await db.refresh(source)
    return LogSourceRead.model_validate(source)


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> None:
    result = await db.execute(select(LogSource).where(LogSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.delete(source)
    await db.commit()
