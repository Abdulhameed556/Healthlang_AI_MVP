"""SQLAlchemy implementation of IClinicalNoteRepository."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.clinical_notes.entities import ClinicalNote
from backend.src.domain.clinical_notes.repositories import IClinicalNoteRepository
from backend.src.infrastructure.database.models.clinical_note import (
    ClinicalNote as ClinicalNoteModel,
)
from backend.src.infrastructure.repositories._mappers import (
    clinical_note_to_entity,
    clinical_note_to_model,
)


class SqlAlchemyClinicalNoteRepository(IClinicalNoteRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, note: ClinicalNote) -> ClinicalNote:
        model = clinical_note_to_model(note)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return clinical_note_to_entity(model)

    async def list_by_encounter_id(self, encounter_id: UUID) -> list[ClinicalNote]:
        result = await self._session.execute(
            select(ClinicalNoteModel)
            .where(ClinicalNoteModel.encounter_id == encounter_id)
            .order_by(ClinicalNoteModel.created_at.asc())
        )
        return [clinical_note_to_entity(model) for model in result.scalars().all()]
