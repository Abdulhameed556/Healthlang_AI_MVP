"""Use-case: permanently remove an Admin Panel user."""
from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from admin.src.core.exceptions import ValidationError
from admin.src.domain.users.entities import AdminRole
from admin.src.domain.users.exceptions import AdminUserNotFoundError, LastAdminError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from admin.src.domain.users.repositories import IAdminUserRepository


class RemoveAdminUserUseCase:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: IAdminUserRepository,
    ) -> None:
        self._session = session
        self._users = user_repository

    async def execute(self, *, user_id: UUID, acting_admin_id: UUID) -> None:
        if user_id == acting_admin_id:
            raise ValidationError("You cannot remove your own admin account")

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise AdminUserNotFoundError("Admin user not found")

        if user.role == AdminRole.SUPER_ADMIN:
            remaining = await self._users.count_by_role(AdminRole.SUPER_ADMIN)
            if remaining <= 1:
                raise LastAdminError("Cannot remove the last Super Admin")

        await self._users.delete(user_id)
        await self._session.commit()
