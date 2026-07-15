"""Domain entities for clinical notes."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class ClinicalNote:
    id: UUID
    encounter_id: UUID
    doctor_id: UUID
    diagnosis: str
    notes: str
    created_at: datetime
