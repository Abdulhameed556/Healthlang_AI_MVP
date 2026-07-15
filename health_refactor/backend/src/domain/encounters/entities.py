"""Domain entities for encounters."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Encounter:
    id: UUID
    patient_id: UUID
    department_id: UUID
    status: str
    checked_in_at: datetime
    created_at: datetime
    updated_at: datetime
    esi_level: int | None = None
    closed_at: datetime | None = None
