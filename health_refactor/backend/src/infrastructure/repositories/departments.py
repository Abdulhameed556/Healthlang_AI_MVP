"""SQLAlchemy implementation of IDepartmentRepository."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.departments.entities import Department
from backend.src.domain.departments.repositories import IDepartmentRepository
from backend.src.infrastructure.database.models.department import Department as DepartmentModel
from backend.src.infrastructure.repositories._mappers import department_to_entity, department_to_model


class SqlAlchemyDepartmentRepository(IDepartmentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, department: Department) -> Department:
        model = department_to_model(department)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return department_to_entity(model)

    async def get_by_id(self, department_id: UUID) -> Department | None:
        result = await self._session.execute(
            select(DepartmentModel).where(DepartmentModel.id == department_id)
        )
        model = result.scalar_one_or_none()
        return department_to_entity(model) if model is not None else None

    async def save(self, department: Department) -> Department:
        model = department_to_model(department)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)
        return department_to_entity(merged)
