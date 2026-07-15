"""Results for creating a prescription."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreatePrescriptionResult:
    prescription_id: UUID
    encounter_id: UUID
    inventory_item_id: UUID
    dosage: str
    status: str
