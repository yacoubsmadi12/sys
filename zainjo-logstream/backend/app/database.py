"""
Async database setup using SQLAlchemy 2.0 with asyncpg.
"""
from typing import AsyncGenerator
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def _async_database_config(url: str) -> tuple[URL, dict[str, object]]:
    """Build an asyncpg URL and translate libpq-only SSL query options."""
    database_url = make_url(url)
    if database_url.drivername in {"postgresql", "postgres"}:
        database_url = database_url.set(drivername="postgresql+asyncpg")

    query = dict(database_url.query)
    sslmode = query.pop("sslmode", None)
    database_url = database_url.set(query=query)

    connect_args: dict[str, object] = {}
    if sslmode:
        connect_args["ssl"] = sslmode not in {"disable", "allow"}
    return database_url, connect_args


database_url, connect_args = _async_database_config(settings.database_url)
engine = create_async_engine(
    database_url,
    connect_args=connect_args,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables (use Alembic migrations in production)."""
    async with engine.begin() as conn:
        from app.models import Base as ModelBase
        await conn.run_sync(ModelBase.metadata.create_all)
