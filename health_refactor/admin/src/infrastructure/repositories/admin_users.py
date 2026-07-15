"""SQLAlchemy implementation of IAdminUserRepository."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus
from admin.src.infrastructure.database.models.admin_user import AdminUser as AdminUserModel


def _to_entity(row: AdminUserModel) -> AdminUser:
    return AdminUser(
        id=row.id,
        email=row.email,
        first_name=row.first_name,
        last_name=row.last_name,
        role=AdminRole(row.role),
        status=AdminUserStatus(row.status),
        password_hash=row.password_hash,
        google_linked=row.google_linked,
        must_change_password=row.must_change_password,
        failed_attempts=row.failed_attempts,
        invited_by=row.invited_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_model(user: AdminUser) -> AdminUserModel:
    return AdminUserModel(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        status=user.status.value,
        password_hash=user.password_hash,
        google_linked=user.google_linked,
        must_change_password=user.must_change_password,
        failed_attempts=user.failed_attempts,
        invited_by=user.invited_by,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


class AdminUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: UUID) -> AdminUser | None:
        row = await self._session.get(AdminUserModel, id)
        return _to_entity(row) if row else None

    async def get_by_email(self, email: str) -> AdminUser | None:
        result = await self._session.execute(
            select(AdminUserModel).where(AdminUserModel.email == email.lower().strip())
        )
        row = result.scalar_one_or_none()
        return _to_entity(row) if row else None

    async def list_all(self) -> list[AdminUser]:
        result = await self._session.execute(select(AdminUserModel))
        return [_to_entity(row) for row in result.scalars().all()]

    async def save(self, user: AdminUser) -> AdminUser:
        row = _to_model(user)
        merged = await self._session.merge(row)
        await self._session.flush()
        await self._session.refresh(merged)
        return _to_entity(merged)

    async def delete(self, id: UUID) -> None:
        row = await self._session.get(AdminUserModel, id)
        if row:
            await self._session.delete(row)

    async def count_all(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(AdminUserModel))
        return int(result.scalar_one())

    async def count_by_role(self, role: AdminRole) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(AdminUserModel)
            .where(AdminUserModel.role == role.value)
        )
        return int(result.scalar_one())
