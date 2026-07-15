"""Results for the department queue view."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class QueueEntry:
    encounter_id: UUID
    patient_id: UUID
    status: str
    esi_level: int | None
    checked_in_at: datetime


@dataclass(frozen=True)
class ListQueueResult:
    entries: list[QueueEntry]
