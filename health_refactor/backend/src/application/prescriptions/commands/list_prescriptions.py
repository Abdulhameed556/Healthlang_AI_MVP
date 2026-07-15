"""Commands for listing an encounter's prescriptions."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ListPrescriptionsCommand:
    encounter_id: UUID
