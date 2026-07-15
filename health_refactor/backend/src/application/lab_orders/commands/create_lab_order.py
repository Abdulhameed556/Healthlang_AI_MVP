"""Commands for creating a lab order."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreateLabOrderCommand:
    encounter_id: UUID
    ordered_by: UUID
    test_type: str
