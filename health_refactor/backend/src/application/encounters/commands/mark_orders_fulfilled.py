"""Commands for marking an encounter's orders fulfilled."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class MarkOrdersFulfilledCommand:
    encounter_id: UUID
