"""Commands for dispensing a prescription."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DispensePrescriptionCommand:
    prescription_id: UUID
    dispensed_by: UUID
