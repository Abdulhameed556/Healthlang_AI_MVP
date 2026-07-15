"""Results for marking an encounter's orders fulfilled."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class MarkOrdersFulfilledResult:
    encounter_id: UUID
    status: str
