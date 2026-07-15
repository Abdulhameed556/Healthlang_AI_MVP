"""Results for dispensing a prescription."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class DispensePrescriptionResult:
    prescription_id: UUID
    status: str
    dispensed_at: datetime
    remaining_stock: int
