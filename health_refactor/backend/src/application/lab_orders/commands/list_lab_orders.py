"""Commands for listing an encounter's lab orders."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ListLabOrdersCommand:
    encounter_id: UUID
