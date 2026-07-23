"""
Filter rule management endpoints.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_current_user, require_admin, get_db
from app.models.user import User
from app.models.source import LogSource
from app.models.filter import FilterRule, BlockedUser
from app.schemas.filter import (
    FilterRuleCreate, FilterRuleRead, FilterRuleUpdate, FilterRuleList,
    BlockedUserCreate, BlockedUserRead,
)

router = APIRouter(prefix="/filters", tags=["Filters"])


@router.get("", response_model=FilterRuleList)
async def list_filters(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
    source_id: str | None = None,
    page: int = 1,
    page_size: int = 100,
) -> FilterRuleList:
    q = select(FilterRule)
    if source_id:
        q = q.where(FilterRule.source_id == source_id)
    count_q = select(func.count()).select_from(FilterRule)
    if source_id:
        count_q = count_q.where(FilterRule.source_id == source_id)

    total = (await db.execute(count_q)).scalar_one() or 0
    offset = (page - 1) * page_size
    result = await db.execute(q.order_by(FilterRule.name).offset(offset).limit(page_size))
    rules = result.scalars().all()

    items = []
    for rule in rules:
        bu_result = await db.execute(
            select(BlockedUser).where(BlockedUser.filter_rule_id == rule.id)
        )
        blocked = bu_result.scalars().all()
        items.append(FilterRuleRead(
            **{c.name: getattr(rule, c.name) for c in rule.__table__.columns},
            blocked_users=[BlockedUserRead.model_validate(b) for b in blocked],
        ))
    return FilterRuleList(items=items, total=total)


@router.get("/{rule_id}", response_model=FilterRuleRead)
async def get_filter(
    rule_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> FilterRuleRead:
    result = await db.execute(select(FilterRule).where(FilterRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Filter rule not found")
    bu_result = await db.execute(
        select(BlockedUser).where(BlockedUser.filter_rule_id == rule.id)
    )
    blocked = bu_result.scalars().all()
    return FilterRuleRead(
        **{c.name: getattr(rule, c.name) for c in rule.__table__.columns},
        blocked_users=[BlockedUserRead.model_validate(b) for b in blocked],
    )


@router.post("", response_model=FilterRuleRead, status_code=201)
async def create_filter(
    body: FilterRuleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> FilterRuleRead:
    # Validate source exists
    src = await db.execute(select(LogSource).where(LogSource.id == body.source_id))
    if not src.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Source not found")

    rule = FilterRule(
        name=body.name,
        source_id=body.source_id,
        description=body.description,
        field=body.field,
        pattern_type=body.pattern_type,
        action=body.action,
        enabled=body.enabled,
    )
    db.add(rule)
    await db.flush()  # get the id

    blocked_users = []
    for pattern in body.patterns:
        bu = BlockedUser(filter_rule_id=rule.id, source_id=body.source_id, pattern=pattern)
        db.add(bu)
        blocked_users.append(bu)

    await db.commit()
    await db.refresh(rule)
    for bu in blocked_users:
        await db.refresh(bu)

    return FilterRuleRead(
        **{c.name: getattr(rule, c.name) for c in rule.__table__.columns},
        blocked_users=[BlockedUserRead.model_validate(bu) for bu in blocked_users],
    )


@router.patch("/{rule_id}", response_model=FilterRuleRead)
async def update_filter(
    rule_id: str,
    body: FilterRuleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> FilterRuleRead:
    result = await db.execute(select(FilterRule).where(FilterRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Filter rule not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(rule, field, value)
    await db.commit()
    await db.refresh(rule)
    bu_result = await db.execute(
        select(BlockedUser).where(BlockedUser.filter_rule_id == rule.id)
    )
    blocked = bu_result.scalars().all()
    return FilterRuleRead(
        **{c.name: getattr(rule, c.name) for c in rule.__table__.columns},
        blocked_users=[BlockedUserRead.model_validate(b) for b in blocked],
    )


@router.delete("/{rule_id}", status_code=204)
async def delete_filter(
    rule_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> None:
    result = await db.execute(select(FilterRule).where(FilterRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Filter rule not found")
    await db.delete(rule)
    await db.commit()


# ── Blocked users management within a rule ──────────────────────────────────

@router.post("/{rule_id}/users", response_model=BlockedUserRead, status_code=201)
async def add_blocked_user(
    rule_id: str,
    body: BlockedUserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> BlockedUserRead:
    result = await db.execute(select(FilterRule).where(FilterRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Filter rule not found")
    bu = BlockedUser(filter_rule_id=rule_id, source_id=rule.source_id, pattern=body.pattern)
    db.add(bu)
    await db.commit()
    await db.refresh(bu)
    return BlockedUserRead.model_validate(bu)


@router.delete("/{rule_id}/users/{user_id}", status_code=204)
async def remove_blocked_user(
    rule_id: str,
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> None:
    result = await db.execute(
        select(BlockedUser).where(
            BlockedUser.filter_rule_id == rule_id,
            BlockedUser.id == user_id,
        )
    )
    bu = result.scalar_one_or_none()
    if not bu:
        raise HTTPException(status_code=404, detail="Blocked user not found")
    await db.delete(bu)
    await db.commit()
