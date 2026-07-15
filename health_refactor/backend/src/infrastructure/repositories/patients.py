"""SQLAlchemy implementation of IPatientRepository."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.patients.entities import Patient
from backend.src.domain.patients.repositories import IPatientRepository
from backend.src.infrastructure.database.models.patient import Patient as PatientModel
from backend.src.infrastructure.repositories._mappers import patient_to_entity, patient_to_model


class SqlAlchemyPatientRepository(IPatientRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, patient: Patient) -> Patient:
        model = patient_to_model(patient)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return patient_to_entity(model)

    async def get_by_id(self, patient_id: UUID) -> Patient | None:
        result = await self._session.execute(
            select(PatientModel).where(PatientModel.id == patient_id)
        )
        model = result.scalar_one_or_none()
        return patient_to_entity(model) if model is not None else None

    async def save(self, patient: Patient) -> Patient:
        model = patient_to_model(patient)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)
        return patient_to_entity(merged)
