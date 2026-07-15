"""Unit tests: infrastructure/repositories/lab_orders.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.domain.lab_orders.entities import LabOrder
from backend.src.domain.lab_orders.value_objects import LabOrderStatus
from backend.src.infrastructure.repositories._mappers import (
    lab_order_to_entity,
    lab_order_to_model,
)
from backend.src.infrastructure.repositories.lab_orders import SqlAlchemyLabOrderRepository


def _scalar_result(*, one_or_none=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = one_or_none
    return result


def _list_result(models):
    result = MagicMock()
    result.scalars.return_value.all.return_value = models
    return result


def _lab_order(**overrides) -> LabOrder:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid4(),
        encounter_id=uuid4(),
        ordered_by=uuid4(),
        test_type="Full blood count",
        status=LabOrderStatus.PENDING.value,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return LabOrder(**defaults)


@pytest.mark.asyncio
async def test_add_persists_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyLabOrderRepository(session)
    entity = _lab_order()

    result = await repo.add(entity)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    assert result == lab_order_to_entity(lab_order_to_model(entity))


@pytest.mark.asyncio
async def test_get_by_id_returns_entity_when_found() -> None:
    session = AsyncMock()
    repo = SqlAlchemyLabOrderRepository(session)
    entity = _lab_order()
    model = lab_order_to_model(entity)
    session.execute.return_value = _scalar_result(one_or_none=model)

    assert await repo.get_by_id(entity.id) == entity


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing() -> None:
    session = AsyncMock()
    repo = SqlAlchemyLabOrderRepository(session)
    session.execute.return_value = _scalar_result(one_or_none=None)

    assert await repo.get_by_id(uuid4()) is None


@pytest.mark.asyncio
async def test_save_merges_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyLabOrderRepository(session)
    entity = _lab_order()
    model = lab_order_to_model(entity)
    session.merge.return_value = model

    result = await repo.save(entity)

    session.merge.assert_awaited_once()
    assert result == lab_order_to_entity(model)


@pytest.mark.asyncio
async def test_list_by_encounter_id_returns_mapped_entities() -> None:
    session = AsyncMock()
    repo = SqlAlchemyLabOrderRepository(session)
    entity = _lab_order()
    model = lab_order_to_model(entity)
    session.execute.return_value = _list_result([model])

    result = await repo.list_by_encounter_id(entity.encounter_id)

    assert result == [lab_order_to_entity(model)]
