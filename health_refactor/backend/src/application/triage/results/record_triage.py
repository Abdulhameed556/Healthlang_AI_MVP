"""Results for recording triage."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RecordTriageResult:
    triage_record_id: UUID
    encounter_id: UUID
    esi_suggested_level: int
    esi_level: int
    was_overridden: bool
