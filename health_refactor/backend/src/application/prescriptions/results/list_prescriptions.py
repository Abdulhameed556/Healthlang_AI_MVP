"""Results for listing an encounter's prescriptions."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PrescriptionSummary:
    prescription_id: UUID
    inventory_item_id: UUID
    dosage: str
    status: str
    created_at: datetime
    dispensed_at: datetime | None


@dataclass(frozen=True)
class ListPrescriptionsResult:
    prescriptions: list[PrescriptionSummary]
