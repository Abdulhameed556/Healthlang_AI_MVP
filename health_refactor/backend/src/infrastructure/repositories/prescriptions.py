"""SQLAlchemy implementation of IPrescriptionRepository."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.prescriptions.entities import Prescription
from backend.src.domain.prescriptions.repositories import IPrescriptionRepository
from backend.src.infrastructure.database.models.prescription import (
    Prescription as PrescriptionModel,
)
from backend.src.infrastructure.repositories._mappers import (
    prescription_to_entity,
    prescription_to_model,
)


class SqlAlchemyPrescriptionRepository(IPrescriptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, prescription: Prescription) -> Prescription:
        model = prescription_to_model(prescription)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return prescription_to_entity(model)

    async def get_by_id(self, prescription_id: UUID) -> Prescription | None:
        result = await self._session.execute(
            select(PrescriptionModel).where(PrescriptionModel.id == prescription_id)
        )
        model = result.scalar_one_or_none()
        return prescription_to_entity(model) if model is not None else None

    async def save(self, prescription: Prescription) -> Prescription:
        model = prescription_to_model(prescription)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)
        return prescription_to_entity(merged)

    async def list_by_encounter_id(self, encounter_id: UUID) -> list[Prescription]:
        result = await self._session.execute(
            select(PrescriptionModel)
            .where(PrescriptionModel.encounter_id == encounter_id)
            .order_by(PrescriptionModel.created_at.asc())
        )
        return [prescription_to_entity(model) for model in result.scalars().all()]
