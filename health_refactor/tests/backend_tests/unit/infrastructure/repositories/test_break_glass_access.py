"""Unit tests: infrastructure/repositories/break_glass_access.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.domain.break_glass.entities import BreakGlassAccess
from backend.src.infrastructure.repositories._mappers import (
    break_glass_access_to_entity,
    break_glass_access_to_model,
)
from backend.src.infrastructure.repositories.break_glass_access import (
    SqlAlchemyBreakGlassAccessRepository,
)


def _scalar_result(*, one_or_none=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = one_or_none
    return result


def _list_result(models):
    result = MagicMock()
    result.scalars.return_value.all.return_value = models
    return result


def _request(**overrides) -> BreakGlassAccess:
    defaults = dict(
        id=uuid4(),
        requesting_user_id=uuid4(),
        target_patient_id=uuid4(),
        reason="Covering for a colleague during an emergency",
        needs_review=True,
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return BreakGlassAccess(**defaults)


@pytest.mark.asyncio
async def test_add_persists_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyBreakGlassAccessRepository(session)
    entity = _request()

    result = await repo.add(entity)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    assert result == break_glass_access_to_entity(break_glass_access_to_model(entity))


@pytest.mark.asyncio
async def test_get_by_id_returns_entity_when_found() -> None:
    session = AsyncMock()
    repo = SqlAlchemyBreakGlassAccessRepository(session)
    entity = _request()
    model = break_glass_access_to_model(entity)
    session.execute.return_value = _scalar_result(one_or_none=model)

    assert await repo.get_by_id(entity.id) == entity


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing() -> None:
    session = AsyncMock()
    repo = SqlAlchemyBreakGlassAccessRepository(session)
    session.execute.return_value = _scalar_result(one_or_none=None)

    assert await repo.get_by_id(uuid4()) is None


@pytest.mark.asyncio
async def test_save_merges_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyBreakGlassAccessRepository(session)
    entity = _request(needs_review=False)
    model = break_glass_access_to_model(entity)
    session.merge.return_value = model

    result = await repo.save(entity)

    session.merge.assert_awaited_once()
    assert result == break_glass_access_to_entity(model)


@pytest.mark.asyncio
async def test_list_needing_review_returns_mapped_entities() -> None:
    session = AsyncMock()
    repo = SqlAlchemyBreakGlassAccessRepository(session)
    entity = _request()
    model = break_glass_access_to_model(entity)
    session.execute.return_value = _list_result([model])

    result = await repo.list_needing_review()

    assert result == [break_glass_access_to_entity(model)]
