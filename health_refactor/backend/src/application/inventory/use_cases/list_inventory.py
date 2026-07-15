"""Use-case: list a department's drug inventory."""
from backend.src.application.inventory.commands.list_inventory import ListInventoryCommand
from backend.src.application.inventory.results.list_inventory import (
    InventoryItemSummary,
    ListInventoryResult,
)
from backend.src.domain.inventory.repositories import IInventoryItemRepository


class ListInventory:
    def __init__(self, inventory_item_repository: IInventoryItemRepository) -> None:
        self._inventory_item_repository = inventory_item_repository

    async def execute(self, command: ListInventoryCommand) -> ListInventoryResult:
        items = await self._inventory_item_repository.list_by_department_id(
            command.department_id
        )
        return ListInventoryResult(
            items=[
                InventoryItemSummary(
                    item_id=item.id,
                    drug_name=item.drug_name,
                    quantity_on_hand=item.quantity_on_hand,
                    reorder_threshold=item.reorder_threshold,
                    low_stock=item.quantity_on_hand <= item.reorder_threshold,
                )
                for item in items
            ]
        )
