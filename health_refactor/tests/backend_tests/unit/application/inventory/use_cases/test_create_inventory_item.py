"""Unit tests: application/inventory/use_cases/create_inventory_item.py"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.inventory.commands.create_inventory_item import (
    CreateInventoryItemCommand,
)
from backend.src.application.inventory.use_cases.create_inventory_item import (
    CreateInventoryItem,
)


@pytest.mark.asyncio
async def test_execute_creates_item_and_commits() -> None:
    repo = AsyncMock()
    repo.add = AsyncMock(side_effect=lambda item: item)
    unit_of_work = AsyncMock()
    unit_of_work.commit = AsyncMock()
    use_case = CreateInventoryItem(
        inventory_item_repository=repo, unit_of_work=unit_of_work
    )
    dept_id = uuid4()

    result = await use_case.execute(
        CreateInventoryItemCommand(
            department_id=dept_id,
            drug_name="Paracetamol 500mg",
            quantity_on_hand=100,
            reorder_threshold=20,
        )
    )

    assert result.department_id == dept_id
    assert result.drug_name == "Paracetamol 500mg"
    assert result.quantity_on_hand == 100
    unit_of_work.commit.assert_awaited_once()
