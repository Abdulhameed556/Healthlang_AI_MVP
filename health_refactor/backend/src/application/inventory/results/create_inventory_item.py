"""Results for creating an inventory item."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreateInventoryItemResult:
    item_id: UUID
    department_id: UUID
    drug_name: str
    quantity_on_hand: int
    reorder_threshold: int
