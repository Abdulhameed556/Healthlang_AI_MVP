"""Commands for creating a clinical note."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreateClinicalNoteCommand:
    encounter_id: UUID
    doctor_id: UUID
    diagnosis: str
    notes: str
