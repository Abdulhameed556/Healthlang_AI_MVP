"""SQLAlchemy implementation of ITriageRecordRepository."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.triage.entities import TriageRecord
from backend.src.domain.triage.repositories import ITriageRecordRepository
from backend.src.infrastructure.database.models.triage_record import (
    TriageRecord as TriageRecordModel,
)
from backend.src.infrastructure.repositories._mappers import (
    triage_record_to_entity,
    triage_record_to_model,
)


class SqlAlchemyTriageRecordRepository(ITriageRecordRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, record: TriageRecord) -> TriageRecord:
        model = triage_record_to_model(record)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return triage_record_to_entity(model)

    async def get_by_encounter_id(self, encounter_id: UUID) -> TriageRecord | None:
        result = await self._session.execute(
            select(TriageRecordModel).where(TriageRecordModel.encounter_id == encounter_id)
        )
        model = result.scalar_one_or_none()
        return triage_record_to_entity(model) if model is not None else None
