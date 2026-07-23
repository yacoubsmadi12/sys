"""
Authentication routes: login, logout, whoami, user management.
"""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_current_user, require_admin, get_db
from app.auth.security import verify_password, get_password_hash, create_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserRead, UserUpdate, UserList

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.hashed_password) or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    token = create_access_token({"sub": user.username, "role": user.role})
    return Token(access_token=token, token_type="bearer", role=user.role, username=user.username)


@router.get("/me", response_model=UserRead)
async def whoami(current_user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    return UserRead.model_validate(current_user)


# ── User management (admin only) ──────────────────────────────────────────────

@router.get("/users", response_model=UserList)
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
    page: int = 1,
    page_size: int = 50,
) -> UserList:
    offset = (page - 1) * page_size
    total_result = await db.execute(select(func.count()).select_from(User))
    total = total_result.scalar_one()
    result = await db.execute(select(User).offset(offset).limit(page_size))
    users = result.scalars().all()
    return UserList(items=[UserRead.model_validate(u) for u in users], total=total)


@router.post("/users", response_model=UserRead, status_code=201)
async def create_user(
    body: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> UserRead:
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(
        username=body.username,
        hashed_password=get_password_hash(body.password),
        full_name=body.full_name,
        email=body.email,
        role=body.role,
        is_active=body.is_active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: str,
    body: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_admin)],
) -> UserRead:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in body.model_dump(exclude_none=True).items():
        if field == "password":
            setattr(user, "hashed_password", get_password_hash(value))
        else:
            setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate(user)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_admin)],
) -> None:
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
