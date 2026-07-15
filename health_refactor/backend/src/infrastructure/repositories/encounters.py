"""SQLAlchemy implementation of IEncounterRepository."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.encounters.entities import Encounter
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.infrastructure.database.models.encounter import Encounter as EncounterModel
from backend.src.infrastructure.repositories._mappers import (
    encounter_to_entity,
    encounter_to_model,
)


class SqlAlchemyEncounterRepository(IEncounterRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, encounter: Encounter) -> Encounter:
        model = encounter_to_model(encounter)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return encounter_to_entity(model)

    async def get_by_id(self, encounter_id: UUID) -> Encounter | None:
        result = await self._session.execute(
            select(EncounterModel).where(EncounterModel.id == encounter_id)
        )
        model = result.scalar_one_or_none()
        return encounter_to_entity(model) if model is not None else None

    async def save(self, encounter: Encounter) -> Encounter:
        model = encounter_to_model(encounter)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)
        return encounter_to_entity(merged)

    async def list_queue(
        self,
        department_id: UUID,
        statuses: list[EncounterStatus],
    ) -> list[Encounter]:
        result = await self._session.execute(
            select(EncounterModel)
            .where(
                EncounterModel.department_id == department_id,
                EncounterModel.status.in_([s.value for s in statuses]),
            )
            .order_by(
                EncounterModel.esi_level.asc().nulls_last(),
                EncounterModel.checked_in_at.asc(),
            )
        )
        return [encounter_to_entity(model) for model in result.scalars().all()]
