"""FastAPI database and repository dependencies."""
from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from admin.src.domain.auth.repositories import IAdminSessionRepository
from admin.src.domain.users.repositories import IAdminUserRepository
from admin.src.infrastructure.database.session import async_session_factory
from admin.src.infrastructure.repositories.admin_sessions import (
    AdminSessionRepository,
)
from admin.src.infrastructure.repositories.admin_users import AdminUserRepository


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_admin_session_repository(
    session: AsyncSession = Depends(get_db),
) -> IAdminSessionRepository:
    return AdminSessionRepository(session)


def get_admin_user_repository(
    session: AsyncSession = Depends(get_db),
) -> IAdminUserRepository:
    return AdminUserRepository(session)
