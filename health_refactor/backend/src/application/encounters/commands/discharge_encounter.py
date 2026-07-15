"""Commands for discharging an encounter."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DischargeEncounterCommand:
    encounter_id: UUID
