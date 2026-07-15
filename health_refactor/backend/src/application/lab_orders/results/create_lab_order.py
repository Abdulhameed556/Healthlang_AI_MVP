"""Results for creating a lab order."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreateLabOrderResult:
    lab_order_id: UUID
    encounter_id: UUID
    test_type: str
    status: str
