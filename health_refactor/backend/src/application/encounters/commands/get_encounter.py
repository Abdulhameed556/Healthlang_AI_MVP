"""Commands for encounter lookup."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetEncounterCommand:
    encounter_id: UUID
