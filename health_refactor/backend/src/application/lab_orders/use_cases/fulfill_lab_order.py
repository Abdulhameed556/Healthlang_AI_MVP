"""Use-case: lab scientist uploads a result for a pending lab order."""
from dataclasses import replace
from datetime import datetime, timezone

from backend.src.application.lab_orders.commands.fulfill_lab_order import (
    FulfillLabOrderCommand,
)
from backend.src.application.lab_orders.results.fulfill_lab_order import (
    FulfillLabOrderResult,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.lab_orders.exceptions import (
    LabOrderAlreadyFulfilledError,
    LabOrderNotFoundError,
)
from backend.src.domain.lab_orders.repositories import ILabOrderRepository
from backend.src.domain.lab_orders.value_objects import LabOrderStatus


class FulfillLabOrder:
    def __init__(
        self,
        lab_order_repository: ILabOrderRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._lab_order_repository = lab_order_repository
        self._unit_of_work = unit_of_work

    async def execute(self, command: FulfillLabOrderCommand) -> FulfillLabOrderResult:
        lab_order = await self._lab_order_repository.get_by_id(command.lab_order_id)
        if lab_order is None:
            raise LabOrderNotFoundError("Lab order not found")

        if lab_order.status == LabOrderStatus.COMPLETED.value:
            raise LabOrderAlreadyFulfilledError("This lab order is already fulfilled")

        now = datetime.now(timezone.utc)
        updated = replace(
            lab_order,
            status=LabOrderStatus.COMPLETED.value,
            result_payload=command.result_payload,
            fulfilled_by=command.fulfilled_by,
            fulfilled_at=now,
            updated_at=now,
        )
        updated = await self._lab_order_repository.save(updated)
        await self._unit_of_work.commit()

        return FulfillLabOrderResult(
            lab_order_id=updated.id,
            status=updated.status,
            result_payload=updated.result_payload,
            fulfilled_at=updated.fulfilled_at,
        )
