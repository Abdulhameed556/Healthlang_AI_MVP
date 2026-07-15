"""Abstract repository interface for encounters."""
from typing import Protocol
from uuid import UUID

from backend.src.domain.encounters.entities import Encounter
from backend.src.domain.encounters.value_objects import EncounterStatus


class IEncounterRepository(Protocol):
    async def get_by_id(self, encounter_id: UUID) -> Encounter | None: ...
    async def add(self, encounter: Encounter) -> Encounter: ...
    async def save(self, encounter: Encounter) -> Encounter: ...
    async def list_queue(
        self,
        department_id: UUID,
        statuses: list[EncounterStatus],
    ) -> list[Encounter]: ...
