"""SQLAlchemy implementation of IUserSessionRepository."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.auth.entities import UserSession
from backend.src.domain.auth.repositories import IUserSessionRepository
from backend.src.infrastructure.database.models.user_session import UserSession as UserSessionModel
from backend.src.infrastructure.repositories._session_mappers import (
    user_session_to_entity,
    user_session_to_model,
)


class SqlAlchemyUserSessionRepository(IUserSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, session_entity: UserSession) -> UserSession:
        model = user_session_to_model(session_entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return user_session_to_entity(model)

    async def get_by_token(self, token: str) -> UserSession | None:
        result = await self._session.execute(
            select(UserSessionModel).where(
                UserSessionModel.token == token,
                UserSessionModel.invalidated_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return user_session_to_entity(model) if model is not None else None

    async def get_by_refresh_token(self, refresh_token: str) -> UserSession | None:
        result = await self._session.execute(
            select(UserSessionModel).where(
                UserSessionModel.refresh_token == refresh_token,
                UserSessionModel.invalidated_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        return user_session_to_entity(model) if model is not None else None

    async def save(self, session_entity: UserSession) -> UserSession:
        model = user_session_to_model(session_entity)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)
        return user_session_to_entity(merged)

    async def invalidate_by_token(self, token: str) -> None:
        now = datetime.now(timezone.utc)
        await self._session.execute(
            update(UserSessionModel)
            .where(
                UserSessionModel.token == token,
                UserSessionModel.invalidated_at.is_(None),
            )
            .values(invalidated_at=now)
        )

    async def invalidate_all_for_user(self, user_id: UUID) -> None:
        now = datetime.now(timezone.utc)
        await self._session.execute(
            update(UserSessionModel)
            .where(
                UserSessionModel.user_id == user_id,
                UserSessionModel.invalidated_at.is_(None),
            )
            .values(invalidated_at=now)
        )
