"""Unit tests: backend/src/infrastructure/database/unit_of_work.py"""
from unittest.mock import AsyncMock

import pytest

from backend.src.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def _make_session() -> AsyncMock:
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_commit_delegates_to_session() -> None:
    session = _make_session()
    uow = SqlAlchemyUnitOfWork(session)

    await uow.commit()

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_aenter_returns_self() -> None:
    session = _make_session()
    uow = SqlAlchemyUnitOfWork(session)

    result = await uow.__aenter__()

    assert result is uow


@pytest.mark.asyncio
async def test_aexit_commits_when_no_exception() -> None:
    session = _make_session()
    uow = SqlAlchemyUnitOfWork(session)

    async with uow:
        pass

    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_aexit_rolls_back_on_exception() -> None:
    session = _make_session()
    uow = SqlAlchemyUnitOfWork(session)

    with pytest.raises(RuntimeError):
        async with uow:
            raise RuntimeError("boom")

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
