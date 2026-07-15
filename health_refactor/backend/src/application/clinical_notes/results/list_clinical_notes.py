"""Results for listing an encounter's clinical notes."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ClinicalNoteSummary:
    note_id: UUID
    doctor_id: UUID
    diagnosis: str
    notes: str
    created_at: datetime


@dataclass(frozen=True)
class ListClinicalNotesResult:
    notes: list[ClinicalNoteSummary]
