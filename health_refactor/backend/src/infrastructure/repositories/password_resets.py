"""SQLAlchemy implementation of IPasswordResetRepository."""
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.auth.entities import PasswordReset
from backend.src.domain.auth.repositories import IPasswordResetRepository
from backend.src.domain.auth.value_objects import PasswordResetStatus
from backend.src.infrastructure.database.models.password_reset import (
    PasswordReset as PasswordResetModel,
)
from backend.src.infrastructure.repositories._password_reset_mappers import (
    password_reset_to_entity,
    password_reset_to_model,
)


class SqlAlchemyPasswordResetRepository(IPasswordResetRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, password_reset: PasswordReset) -> PasswordReset:
        model = password_reset_to_model(password_reset)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return password_reset_to_entity(model)

    async def save(self, password_reset: PasswordReset) -> PasswordReset:
        model = password_reset_to_model(password_reset)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)
        return password_reset_to_entity(merged)

    async def list_pending_for_user_ids(
        self, user_ids: list[UUID]
    ) -> list[PasswordReset]:
        if not user_ids:
            return []
        result = await self._session.execute(
            select(PasswordResetModel).where(
                PasswordResetModel.user_id.in_(user_ids),
                PasswordResetModel.status == PasswordResetStatus.PENDING,
            )
        )
        return [password_reset_to_entity(model) for model in result.scalars().all()]

    async def expire_pending_for_user(self, user_id: UUID) -> None:
        await self._session.execute(
            update(PasswordResetModel)
            .where(
                PasswordResetModel.user_id == user_id,
                PasswordResetModel.status == PasswordResetStatus.PENDING,
            )
            .values(status=PasswordResetStatus.EXPIRED)
        )
