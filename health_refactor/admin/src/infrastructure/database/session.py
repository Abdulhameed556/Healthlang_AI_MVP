"""Admin async DB session.

Admin and backend run in one process against one database, so they share a
single engine and session factory (one connection pool). This module re-exports
the backend's session primitives rather than building a second engine.
"""
from backend.src.infrastructure.database.session import (
    async_session_factory,
    build_async_engine,
    close_database_connection,
    engine,
    get_async_session,
    verify_database_connection,
)

__all__ = [
    "async_session_factory",
    "build_async_engine",
    "close_database_connection",
    "engine",
    "get_async_session",
    "verify_database_connection",
]
