"""Unit tests: infrastructure/database/unit_of_work.py (admin panel)."""
from unittest.mock import AsyncMock

import pytest

from admin.src.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


@pytest.mark.asyncio
async def test_commit_delegates_to_session() -> None:
    session = AsyncMock()
    uow = SqlAlchemyUnitOfWork(session)

    await uow.commit()

    session.commit.assert_awaited_once()
