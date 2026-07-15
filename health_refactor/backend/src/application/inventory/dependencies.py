"""FastAPI dependency-injection providers for inventory use-cases."""
from fastapi import Depends

from backend.src.application.inventory.use_cases.create_inventory_item import (
    CreateInventoryItem,
)
from backend.src.application.inventory.use_cases.list_inventory import ListInventory
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.inventory.repositories import IInventoryItemRepository
from backend.src.infrastructure.database.dependencies import (
    get_inventory_item_repository,
    get_unit_of_work,
)


def get_create_inventory_item(
    inventory_item_repository: IInventoryItemRepository = Depends(
        get_inventory_item_repository
    ),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> CreateInventoryItem:
    return CreateInventoryItem(
        inventory_item_repository=inventory_item_repository,
        unit_of_work=unit_of_work,
    )


def get_list_inventory(
    inventory_item_repository: IInventoryItemRepository = Depends(
        get_inventory_item_repository
    ),
) -> ListInventory:
    return ListInventory(inventory_item_repository=inventory_item_repository)
