"""Unit tests: infrastructure/repositories/user_sessions.py"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.domain.auth.entities import UserSession
from backend.src.infrastructure.repositories._session_mappers import (
    user_session_to_entity,
    user_session_to_model,
)
from backend.src.infrastructure.repositories.user_sessions import SqlAlchemyUserSessionRepository


def _scalar_result(*, one_or_none=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = one_or_none
    return result


@pytest.fixture()
def session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture()
def repo(session: AsyncMock) -> SqlAlchemyUserSessionRepository:
    return SqlAlchemyUserSessionRepository(session)


@pytest.mark.asyncio
async def test_add_persists_session(repo: SqlAlchemyUserSessionRepository, session: AsyncMock) -> None:
    now = datetime.now(timezone.utc)
    entity = UserSession(
        id=uuid4(),
        user_id=uuid4(),
        token="jwt-token",
        created_at=now,
        expires_at=now + timedelta(hours=1),
    )

    async def _refresh(model: object) -> None:
        return None

    session.refresh.side_effect = _refresh
    result = await repo.add(entity)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    assert result == user_session_to_entity(user_session_to_model(entity))


@pytest.mark.asyncio
async def test_get_by_token_returns_none_when_missing(
    repo: SqlAlchemyUserSessionRepository, session: AsyncMock
) -> None:
    session.execute.return_value = _scalar_result(one_or_none=None)

    result = await repo.get_by_token("missing")

    assert result is None


@pytest.mark.asyncio
async def test_invalidate_by_token_executes_update(
    repo: SqlAlchemyUserSessionRepository, session: AsyncMock
) -> None:
    await repo.invalidate_by_token("jwt-token")

    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_invalidate_all_for_user_executes_update(
    repo: SqlAlchemyUserSessionRepository, session: AsyncMock
) -> None:
    await repo.invalidate_all_for_user(uuid4())

    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_refresh_token_returns_none_when_missing(
    repo: SqlAlchemyUserSessionRepository, session: AsyncMock
) -> None:
    session.execute.return_value = _scalar_result(one_or_none=None)

    assert await repo.get_by_refresh_token("missing") is None


@pytest.mark.asyncio
async def test_save_merges_and_returns_entity(
    repo: SqlAlchemyUserSessionRepository, session: AsyncMock
) -> None:
    now = datetime.now(timezone.utc)
    entity = UserSession(
        id=uuid4(),
        user_id=uuid4(),
        token="access-token",
        created_at=now,
        expires_at=now + timedelta(hours=1),
        refresh_token="refresh-token",
        refresh_expires_at=now + timedelta(days=3),
    )
    model = user_session_to_model(entity)
    session.merge.return_value = model

    async def _refresh(merged: object) -> None:
        return None

    session.refresh.side_effect = _refresh
    result = await repo.save(entity)

    session.merge.assert_awaited_once()
    assert result.refresh_token == "refresh-token"
