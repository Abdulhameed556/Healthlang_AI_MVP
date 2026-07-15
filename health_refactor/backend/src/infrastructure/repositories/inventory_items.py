"""SQLAlchemy implementation of IInventoryItemRepository."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.inventory.entities import InventoryItem
from backend.src.domain.inventory.repositories import IInventoryItemRepository
from backend.src.infrastructure.database.models.inventory_item import (
    InventoryItem as InventoryItemModel,
)
from backend.src.infrastructure.repositories._mappers import (
    inventory_item_to_entity,
    inventory_item_to_model,
)


class SqlAlchemyInventoryItemRepository(IInventoryItemRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, item: InventoryItem) -> InventoryItem:
        model = inventory_item_to_model(item)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return inventory_item_to_entity(model)

    async def get_by_id(self, item_id: UUID) -> InventoryItem | None:
        result = await self._session.execute(
            select(InventoryItemModel).where(InventoryItemModel.id == item_id)
        )
        model = result.scalar_one_or_none()
        return inventory_item_to_entity(model) if model is not None else None

    async def save(self, item: InventoryItem) -> InventoryItem:
        model = inventory_item_to_model(item)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)
        return inventory_item_to_entity(merged)

    async def list_by_department_id(self, department_id: UUID) -> list[InventoryItem]:
        result = await self._session.execute(
            select(InventoryItemModel)
            .where(InventoryItemModel.department_id == department_id)
            .order_by(InventoryItemModel.drug_name.asc())
        )
        return [inventory_item_to_entity(model) for model in result.scalars().all()]
