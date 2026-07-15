"""Unit tests: infrastructure/repositories/inventory_items.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.domain.inventory.entities import InventoryItem
from backend.src.infrastructure.repositories._mappers import (
    inventory_item_to_entity,
    inventory_item_to_model,
)
from backend.src.infrastructure.repositories.inventory_items import (
    SqlAlchemyInventoryItemRepository,
)


def _scalar_result(*, one_or_none=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = one_or_none
    return result


def _list_result(models):
    result = MagicMock()
    result.scalars.return_value.all.return_value = models
    return result


def _item(**overrides) -> InventoryItem:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid4(),
        department_id=uuid4(),
        drug_name="Paracetamol 500mg",
        quantity_on_hand=100,
        reorder_threshold=20,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return InventoryItem(**defaults)


@pytest.mark.asyncio
async def test_add_persists_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyInventoryItemRepository(session)
    entity = _item()

    result = await repo.add(entity)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    assert result == inventory_item_to_entity(inventory_item_to_model(entity))


@pytest.mark.asyncio
async def test_get_by_id_returns_entity_when_found() -> None:
    session = AsyncMock()
    repo = SqlAlchemyInventoryItemRepository(session)
    entity = _item()
    model = inventory_item_to_model(entity)
    session.execute.return_value = _scalar_result(one_or_none=model)

    assert await repo.get_by_id(entity.id) == entity


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing() -> None:
    session = AsyncMock()
    repo = SqlAlchemyInventoryItemRepository(session)
    session.execute.return_value = _scalar_result(one_or_none=None)

    assert await repo.get_by_id(uuid4()) is None


@pytest.mark.asyncio
async def test_save_merges_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyInventoryItemRepository(session)
    entity = _item()
    model = inventory_item_to_model(entity)
    session.merge.return_value = model

    result = await repo.save(entity)

    session.merge.assert_awaited_once()
    assert result == inventory_item_to_entity(model)


@pytest.mark.asyncio
async def test_list_by_department_id_returns_mapped_entities() -> None:
    session = AsyncMock()
    repo = SqlAlchemyInventoryItemRepository(session)
    entity = _item()
    model = inventory_item_to_model(entity)
    session.execute.return_value = _list_result([model])

    result = await repo.list_by_department_id(entity.department_id)

    assert result == [inventory_item_to_entity(model)]
