"""Results for encounter lookup."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class GetEncounterResult:
    encounter_id: UUID
    patient_id: UUID
    department_id: UUID
    status: str
    esi_level: int | None
    checked_in_at: datetime
    closed_at: datetime | None
