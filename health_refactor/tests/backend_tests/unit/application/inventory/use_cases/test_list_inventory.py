"""Unit tests: application/inventory/use_cases/list_inventory.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.inventory.commands.list_inventory import ListInventoryCommand
from backend.src.application.inventory.use_cases.list_inventory import ListInventory
from backend.src.domain.inventory.entities import InventoryItem


def _item(quantity_on_hand: int, reorder_threshold: int) -> InventoryItem:
    now = datetime.now(timezone.utc)
    return InventoryItem(
        id=uuid4(),
        department_id=uuid4(),
        drug_name="Paracetamol 500mg",
        quantity_on_hand=quantity_on_hand,
        reorder_threshold=reorder_threshold,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_execute_flags_low_stock() -> None:
    repo = AsyncMock()
    dept_id = uuid4()
    repo.list_by_department_id = AsyncMock(
        return_value=[_item(quantity_on_hand=5, reorder_threshold=20)]
    )
    use_case = ListInventory(inventory_item_repository=repo)

    result = await use_case.execute(ListInventoryCommand(department_id=dept_id))

    assert len(result.items) == 1
    assert result.items[0].low_stock is True


@pytest.mark.asyncio
async def test_execute_does_not_flag_healthy_stock() -> None:
    repo = AsyncMock()
    repo.list_by_department_id = AsyncMock(
        return_value=[_item(quantity_on_hand=100, reorder_threshold=20)]
    )
    use_case = ListInventory(inventory_item_repository=repo)

    result = await use_case.execute(ListInventoryCommand(department_id=uuid4()))

    assert result.items[0].low_stock is False
