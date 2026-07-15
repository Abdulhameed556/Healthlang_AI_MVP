"""SQLAlchemy implementation of IBreakGlassAccessRepository."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.break_glass.entities import BreakGlassAccess
from backend.src.domain.break_glass.repositories import IBreakGlassAccessRepository
from backend.src.infrastructure.database.models.break_glass_access import (
    BreakGlassAccess as BreakGlassAccessModel,
)
from backend.src.infrastructure.repositories._mappers import (
    break_glass_access_to_entity,
    break_glass_access_to_model,
)


class SqlAlchemyBreakGlassAccessRepository(IBreakGlassAccessRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, request: BreakGlassAccess) -> BreakGlassAccess:
        model = break_glass_access_to_model(request)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return break_glass_access_to_entity(model)

    async def get_by_id(self, request_id: UUID) -> BreakGlassAccess | None:
        result = await self._session.execute(
            select(BreakGlassAccessModel).where(BreakGlassAccessModel.id == request_id)
        )
        model = result.scalar_one_or_none()
        return break_glass_access_to_entity(model) if model is not None else None

    async def save(self, request: BreakGlassAccess) -> BreakGlassAccess:
        model = break_glass_access_to_model(request)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)
        return break_glass_access_to_entity(merged)

    async def list_needing_review(self) -> list[BreakGlassAccess]:
        result = await self._session.execute(
            select(BreakGlassAccessModel)
            .where(BreakGlassAccessModel.needs_review.is_(True))
            .order_by(BreakGlassAccessModel.created_at.asc())
        )
        return [break_glass_access_to_entity(model) for model in result.scalars().all()]
