"""Unit tests: infrastructure/database/session.py"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.src.infrastructure.database import session as db_session


@pytest.mark.asyncio
async def test_verify_database_connection_executes_select(monkeypatch) -> None:
    connection = AsyncMock()
    connection.execute = AsyncMock()

    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=connection)
    context.__aexit__ = AsyncMock(return_value=None)

    engine = MagicMock()
    engine.connect.return_value = context
    monkeypatch.setattr(db_session, "engine", engine)

    await db_session.verify_database_connection()
    connection.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_database_connection_disposes_engine(monkeypatch) -> None:
    engine = MagicMock()
    engine.dispose = AsyncMock()
    monkeypatch.setattr(db_session, "engine", engine)

    await db_session.close_database_connection()
    engine.dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_async_session_yields_session(monkeypatch) -> None:
    fake_session = AsyncMock()

    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=fake_session)
    context.__aexit__ = AsyncMock(return_value=None)

    factory = MagicMock(return_value=context)
    monkeypatch.setattr(db_session, "async_session_factory", factory)

    generator = db_session.get_async_session()
    session = await generator.__anext__()
    assert session is fake_session

    with pytest.raises(StopAsyncIteration):
        await generator.__anext__()
