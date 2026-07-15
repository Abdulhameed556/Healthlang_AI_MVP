"""Use-case: add a drug to the department's inventory."""
from datetime import datetime, timezone
from uuid import uuid4

from backend.src.application.inventory.commands.create_inventory_item import (
    CreateInventoryItemCommand,
)
from backend.src.application.inventory.results.create_inventory_item import (
    CreateInventoryItemResult,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.inventory.entities import InventoryItem
from backend.src.domain.inventory.repositories import IInventoryItemRepository


class CreateInventoryItem:
    def __init__(
        self,
        inventory_item_repository: IInventoryItemRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._inventory_item_repository = inventory_item_repository
        self._unit_of_work = unit_of_work

    async def execute(
        self, command: CreateInventoryItemCommand
    ) -> CreateInventoryItemResult:
        now = datetime.now(timezone.utc)
        item = InventoryItem(
            id=uuid4(),
            department_id=command.department_id,
            drug_name=command.drug_name,
            quantity_on_hand=command.quantity_on_hand,
            reorder_threshold=command.reorder_threshold,
            created_at=now,
            updated_at=now,
        )
        item = await self._inventory_item_repository.add(item)
        await self._unit_of_work.commit()

        return CreateInventoryItemResult(
            item_id=item.id,
            department_id=item.department_id,
            drug_name=item.drug_name,
            quantity_on_hand=item.quantity_on_hand,
            reorder_threshold=item.reorder_threshold,
        )
