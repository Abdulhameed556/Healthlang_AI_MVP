"""Commands for creating a prescription."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreatePrescriptionCommand:
    encounter_id: UUID
    ordered_by: UUID
    inventory_item_id: UUID
    dosage: str
