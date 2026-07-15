"""Results for listing a department's inventory."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class InventoryItemSummary:
    item_id: UUID
    drug_name: str
    quantity_on_hand: int
    reorder_threshold: int
    low_stock: bool


@dataclass(frozen=True)
class ListInventoryResult:
    items: list[InventoryItemSummary]
