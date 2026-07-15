"""Commands for listing an encounter's clinical notes."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ListClinicalNotesCommand:
    encounter_id: UUID
