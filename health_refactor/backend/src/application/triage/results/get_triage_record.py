"""Results for triage record lookup."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class GetTriageRecordResult:
    triage_record_id: UUID
    encounter_id: UUID
    recorded_by: UUID
    bp_systolic: int
    bp_diastolic: int
    pulse: int
    respiratory_rate: int
    temperature: float
    esi_suggested_level: int
    esi_level: int
    created_at: datetime
    weight_kg: float | None = None
    override_reason: str | None = None
