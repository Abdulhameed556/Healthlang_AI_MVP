"""Async SQLAlchemy session factory."""
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from backend.src.core.config import settings


def build_async_engine() -> AsyncEngine:
    """
    Create the async engine with pool settings for remote Postgres (e.g. Aiven).

    pool_pre_ping: discard stale connections before use (idle timeout / network blips).
    pool_recycle: proactively refresh connections before the host closes them.

    When ``database_use_null_pool`` is set (the Dramatiq worker), pooling is
    disabled entirely: each task runs in its own short-lived asyncio loop, and a
    connection pinned to a previous, now-closed loop raises "Event loop is closed"
    / "attached to a different loop" on reuse. NullPool opens a fresh connection
    per checkout on the current loop and closes it on return.
    """
    if settings.database_use_null_pool:
        return create_async_engine(
            settings.database_url,
            echo=settings.database_sql_echo,
            poolclass=NullPool,
        )
    return create_async_engine(
        settings.database_url,
        echo=settings.database_sql_echo,
        pool_pre_ping=settings.database_pool_pre_ping,
        pool_recycle=settings.database_pool_recycle,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )


engine = build_async_engine()
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def verify_database_connection() -> None:
    """Raise on startup if the database is unreachable."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def close_database_connection() -> None:
    await engine.dispose()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
