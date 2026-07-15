"""Results for creating a clinical note."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class CreateClinicalNoteResult:
    note_id: UUID
    encounter_id: UUID
    diagnosis: str
    notes: str
    created_at: datetime
