"""Commands for recording triage."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RecordTriageCommand:
    encounter_id: UUID
    recorded_by: UUID
    bp_systolic: int
    bp_diastolic: int
    pulse: int
    respiratory_rate: int
    temperature: float
    weight_kg: float | None = None
    final_esi_level: int | None = None
    override_reason: str | None = None
