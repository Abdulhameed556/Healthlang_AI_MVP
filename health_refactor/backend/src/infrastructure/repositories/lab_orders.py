"""SQLAlchemy implementation of ILabOrderRepository."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.lab_orders.entities import LabOrder
from backend.src.domain.lab_orders.repositories import ILabOrderRepository
from backend.src.infrastructure.database.models.lab_order import LabOrder as LabOrderModel
from backend.src.infrastructure.repositories._mappers import (
    lab_order_to_entity,
    lab_order_to_model,
)


class SqlAlchemyLabOrderRepository(ILabOrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, lab_order: LabOrder) -> LabOrder:
        model = lab_order_to_model(lab_order)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return lab_order_to_entity(model)

    async def get_by_id(self, lab_order_id: UUID) -> LabOrder | None:
        result = await self._session.execute(
            select(LabOrderModel).where(LabOrderModel.id == lab_order_id)
        )
        model = result.scalar_one_or_none()
        return lab_order_to_entity(model) if model is not None else None

    async def save(self, lab_order: LabOrder) -> LabOrder:
        model = lab_order_to_model(lab_order)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)
        return lab_order_to_entity(merged)

    async def list_by_encounter_id(self, encounter_id: UUID) -> list[LabOrder]:
        result = await self._session.execute(
            select(LabOrderModel)
            .where(LabOrderModel.encounter_id == encounter_id)
            .order_by(LabOrderModel.created_at.asc())
        )
        return [lab_order_to_entity(model) for model in result.scalars().all()]
