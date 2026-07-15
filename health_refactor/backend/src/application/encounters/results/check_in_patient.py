"""Results for patient check-in."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class CheckInPatientResult:
    encounter_id: UUID
    patient_id: UUID
    department_id: UUID
    status: str
    checked_in_at: datetime
