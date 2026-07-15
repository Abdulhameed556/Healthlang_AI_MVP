"""SQLAlchemy implementation of IAdminSessionRepository.

The ``token`` column stores a SHA256 hash of the issued JWT, never the raw
token — a leaked DB row is therefore not a usable credential. Callers pass the
hash (see ``admin.src.core.security`` / the login use-case) to look up or invalidate.
"""
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from admin.src.domain.auth.entities import AdminSession
from admin.src.infrastructure.database.models.admin_session import (
    AdminSession as AdminSessionModel,
)


def _to_entity(row: AdminSessionModel) -> AdminSession:
    return AdminSession(
        id=row.id,
        user_id=row.user_id,
        token=row.token,
        created_at=row.created_at,
        expires_at=row.expires_at,
        invalidated_at=row.invalidated_at,
    )


def _to_model(session: AdminSession) -> AdminSessionModel:
    return AdminSessionModel(
        id=session.id,
        user_id=session.user_id,
        token=session.token,
        created_at=session.created_at,
        expires_at=session.expires_at,
        invalidated_at=session.invalidated_at,
    )


class AdminSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_token(self, token: str) -> AdminSession | None:
        result = await self._session.execute(
            select(AdminSessionModel).where(AdminSessionModel.token == token)
        )
        row = result.scalar_one_or_none()
        return _to_entity(row) if row else None

    async def save(self, session: AdminSession) -> AdminSession:
        row = _to_model(session)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_entity(row)

    async def invalidate(self, token: str) -> None:
        await self._session.execute(
            update(AdminSessionModel)
            .where(
                AdminSessionModel.token == token,
                AdminSessionModel.invalidated_at.is_(None),
            )
            .values(invalidated_at=datetime.now(timezone.utc))
        )
