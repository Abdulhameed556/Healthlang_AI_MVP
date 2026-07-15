"""Domain entities for inventory."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class InventoryItem:
    id: UUID
    department_id: UUID
    drug_name: str
    quantity_on_hand: int
    reorder_threshold: int
    created_at: datetime
    updated_at: datetime
