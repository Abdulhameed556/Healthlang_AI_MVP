"""Unit tests: application/lab_orders/use_cases/list_lab_orders.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.lab_orders.commands.list_lab_orders import (
    ListLabOrdersCommand,
)
from backend.src.application.lab_orders.use_cases.list_lab_orders import ListLabOrders
from backend.src.domain.lab_orders.entities import LabOrder
from backend.src.domain.lab_orders.value_objects import LabOrderStatus


@pytest.mark.asyncio
async def test_execute_returns_orders() -> None:
    repo = AsyncMock()
    encounter_id = uuid4()
    order = LabOrder(
        id=uuid4(),
        encounter_id=encounter_id,
        ordered_by=uuid4(),
        test_type="Full blood count",
        status=LabOrderStatus.PENDING.value,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repo.list_by_encounter_id = AsyncMock(return_value=[order])
    use_case = ListLabOrders(lab_order_repository=repo)

    result = await use_case.execute(ListLabOrdersCommand(encounter_id=encounter_id))

    assert len(result.orders) == 1
    assert result.orders[0].test_type == "Full blood count"


@pytest.mark.asyncio
async def test_execute_returns_empty_when_none() -> None:
    repo = AsyncMock()
    repo.list_by_encounter_id = AsyncMock(return_value=[])
    use_case = ListLabOrders(lab_order_repository=repo)

    result = await use_case.execute(ListLabOrdersCommand(encounter_id=uuid4()))

    assert result.orders == []
