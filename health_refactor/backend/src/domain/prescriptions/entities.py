"""Domain entities for prescriptions."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Prescription:
    id: UUID
    encounter_id: UUID
    ordered_by: UUID
    inventory_item_id: UUID
    dosage: str
    status: str
    created_at: datetime
    updated_at: datetime
    dispensed_by: UUID | None = None
    dispensed_at: datetime | None = None
