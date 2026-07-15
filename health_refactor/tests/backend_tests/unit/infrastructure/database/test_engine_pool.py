"""Unit tests: database engine pool configuration."""
from unittest.mock import patch

from sqlalchemy.pool import NullPool

from backend.src.infrastructure.database import session as db_session


def test_build_async_engine_enables_pool_pre_ping_and_recycle() -> None:
    with patch.object(
        db_session.settings,
        "database_url",
        "postgresql+asyncpg://localhost/dashboard",
    ), patch.object(db_session.settings, "database_sql_echo", False), patch.object(
        db_session.settings, "database_use_null_pool", False
    ), patch.object(
        db_session.settings, "database_pool_pre_ping", True
    ), patch.object(
        db_session.settings, "database_pool_recycle", 300
    ), patch.object(
        db_session.settings, "database_pool_size", 5
    ), patch.object(
        db_session.settings, "database_max_overflow", 10
    ), patch(
        "backend.src.infrastructure.database.session.create_async_engine"
    ) as create_engine:
        db_session.build_async_engine()
        create_engine.assert_called_once_with(
            "postgresql+asyncpg://localhost/dashboard",
            echo=False,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10,
        )


def test_build_async_engine_uses_null_pool_for_worker() -> None:
    with patch.object(
        db_session.settings,
        "database_url",
        "postgresql+asyncpg://localhost/dashboard",
    ), patch.object(db_session.settings, "database_sql_echo", False), patch.object(
        db_session.settings, "database_use_null_pool", True
    ), patch(
        "backend.src.infrastructure.database.session.create_async_engine"
    ) as create_engine:
        db_session.build_async_engine()
        create_engine.assert_called_once_with(
            "postgresql+asyncpg://localhost/dashboard",
            echo=False,
            poolclass=NullPool,
        )
