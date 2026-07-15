"""Unit tests: infrastructure/database/dependencies.py (admin panel)."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from admin.src.infrastructure.database import dependencies as db_dependencies
from admin.src.infrastructure.repositories.admin_sessions import AdminSessionRepository
from admin.src.infrastructure.repositories.admin_users import AdminUserRepository


def _fake_factory(monkeypatch):
    fake_session = AsyncMock()
    fake_session.commit = AsyncMock()
    fake_session.rollback = AsyncMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=fake_session)
    context.__aexit__ = AsyncMock(return_value=None)
    monkeypatch.setattr(
        db_dependencies, "async_session_factory", MagicMock(return_value=context)
    )
    return fake_session


@pytest.mark.asyncio
async def test_get_db_yields_session_and_commits(monkeypatch) -> None:
    fake_session = _fake_factory(monkeypatch)

    generator = db_dependencies.get_db()
    session = await generator.__anext__()
    assert session is fake_session

    with pytest.raises(StopAsyncIteration):
        await generator.__anext__()

    fake_session.commit.assert_awaited_once()
    fake_session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_db_rolls_back_on_exception(monkeypatch) -> None:
    fake_session = _fake_factory(monkeypatch)

    generator = db_dependencies.get_db()
    await generator.__anext__()

    with pytest.raises(RuntimeError, match="boom"):
        await generator.athrow(RuntimeError("boom"))

    fake_session.rollback.assert_awaited_once()
    fake_session.commit.assert_not_awaited()


def test_repository_factories_return_impls() -> None:
    session = MagicMock()
    assert isinstance(
        db_dependencies.get_admin_session_repository(session), AdminSessionRepository
    )
    assert isinstance(
        db_dependencies.get_admin_user_repository(session), AdminUserRepository
    )
