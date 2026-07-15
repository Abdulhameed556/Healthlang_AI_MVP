"""Results for discharging an encounter."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class DischargeEncounterResult:
    encounter_id: UUID
    status: str
    closed_at: datetime
