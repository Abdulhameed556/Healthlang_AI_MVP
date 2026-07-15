"""Use-case: list an encounter's lab orders, oldest first."""
from backend.src.application.lab_orders.commands.list_lab_orders import (
    ListLabOrdersCommand,
)
from backend.src.application.lab_orders.results.list_lab_orders import (
    LabOrderSummary,
    ListLabOrdersResult,
)
from backend.src.domain.lab_orders.repositories import ILabOrderRepository


class ListLabOrders:
    def __init__(self, lab_order_repository: ILabOrderRepository) -> None:
        self._lab_order_repository = lab_order_repository

    async def execute(self, command: ListLabOrdersCommand) -> ListLabOrdersResult:
        orders = await self._lab_order_repository.list_by_encounter_id(
            command.encounter_id
        )
        return ListLabOrdersResult(
            orders=[
                LabOrderSummary(
                    lab_order_id=order.id,
                    test_type=order.test_type,
                    status=order.status,
                    result_payload=order.result_payload,
                    created_at=order.created_at,
                    fulfilled_at=order.fulfilled_at,
                )
                for order in orders
            ]
        )
