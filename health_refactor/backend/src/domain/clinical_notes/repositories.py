"""Abstract repository interface for clinical notes."""
from typing import Protocol
from uuid import UUID

from backend.src.domain.clinical_notes.entities import ClinicalNote


class IClinicalNoteRepository(Protocol):
    async def add(self, note: ClinicalNote) -> ClinicalNote: ...
    async def list_by_encounter_id(self, encounter_id: UUID) -> list[ClinicalNote]: ...
