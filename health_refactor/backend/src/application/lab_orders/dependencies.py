"""FastAPI dependency-injection providers for lab_orders use-cases."""
from fastapi import Depends

from backend.src.application.lab_orders.use_cases.create_lab_order import CreateLabOrder
from backend.src.application.lab_orders.use_cases.fulfill_lab_order import FulfillLabOrder
from backend.src.application.lab_orders.use_cases.list_lab_orders import ListLabOrders
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.domain.lab_orders.repositories import ILabOrderRepository
from backend.src.infrastructure.database.dependencies import (
    get_encounter_repository,
    get_lab_order_repository,
    get_unit_of_work,
)


def get_create_lab_order(
    lab_order_repository: ILabOrderRepository = Depends(get_lab_order_repository),
    encounter_repository: IEncounterRepository = Depends(get_encounter_repository),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> CreateLabOrder:
    return CreateLabOrder(
        lab_order_repository=lab_order_repository,
        encounter_repository=encounter_repository,
        unit_of_work=unit_of_work,
    )


def get_fulfill_lab_order(
    lab_order_repository: ILabOrderRepository = Depends(get_lab_order_repository),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> FulfillLabOrder:
    return FulfillLabOrder(
        lab_order_repository=lab_order_repository,
        unit_of_work=unit_of_work,
    )


def get_list_lab_orders(
    lab_order_repository: ILabOrderRepository = Depends(get_lab_order_repository),
) -> ListLabOrders:
    return ListLabOrders(lab_order_repository=lab_order_repository)
