"""Unit tests: application/lab_orders/use_cases/fulfill_lab_order.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.lab_orders.commands.fulfill_lab_order import (
    FulfillLabOrderCommand,
)
from backend.src.application.lab_orders.use_cases.fulfill_lab_order import FulfillLabOrder
from backend.src.domain.lab_orders.entities import LabOrder
from backend.src.domain.lab_orders.exceptions import (
    LabOrderAlreadyFulfilledError,
    LabOrderNotFoundError,
)
from backend.src.domain.lab_orders.value_objects import LabOrderStatus


def _lab_order(status: LabOrderStatus = LabOrderStatus.PENDING) -> LabOrder:
    now = datetime.now(timezone.utc)
    return LabOrder(
        id=uuid4(),
        encounter_id=uuid4(),
        ordered_by=uuid4(),
        test_type="Full blood count",
        status=status.value,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture()
def lab_order_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.save = AsyncMock(side_effect=lambda order: order)
    return repo


@pytest.fixture()
def unit_of_work() -> AsyncMock:
    uow = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture()
def use_case(lab_order_repository, unit_of_work) -> FulfillLabOrder:
    return FulfillLabOrder(
        lab_order_repository=lab_order_repository, unit_of_work=unit_of_work
    )


@pytest.mark.asyncio
async def test_execute_marks_completed_with_result(
    use_case: FulfillLabOrder, lab_order_repository, unit_of_work
) -> None:
    order = _lab_order()
    lab_order_repository.get_by_id = AsyncMock(return_value=order)

    result = await use_case.execute(
        FulfillLabOrderCommand(
            lab_order_id=order.id, fulfilled_by=uuid4(), result_payload="Normal"
        )
    )

    assert result.status == LabOrderStatus.COMPLETED.value
    assert result.result_payload == "Normal"
    unit_of_work.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_raises_when_missing(
    use_case: FulfillLabOrder, lab_order_repository
) -> None:
    lab_order_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(LabOrderNotFoundError):
        await use_case.execute(
            FulfillLabOrderCommand(
                lab_order_id=uuid4(), fulfilled_by=uuid4(), result_payload="x"
            )
        )


@pytest.mark.asyncio
async def test_execute_rejects_already_fulfilled(
    use_case: FulfillLabOrder, lab_order_repository
) -> None:
    order = _lab_order(status=LabOrderStatus.COMPLETED)
    lab_order_repository.get_by_id = AsyncMock(return_value=order)

    with pytest.raises(LabOrderAlreadyFulfilledError):
        await use_case.execute(
            FulfillLabOrderCommand(
                lab_order_id=order.id, fulfilled_by=uuid4(), result_payload="x"
            )
        )
