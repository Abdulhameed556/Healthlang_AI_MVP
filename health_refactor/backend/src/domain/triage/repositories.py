"""Abstract repository interface for triage records."""
from typing import Protocol
from uuid import UUID

from backend.src.domain.triage.entities import TriageRecord


class ITriageRecordRepository(Protocol):
    async def get_by_encounter_id(self, encounter_id: UUID) -> TriageRecord | None: ...
    async def add(self, record: TriageRecord) -> TriageRecord: ...
