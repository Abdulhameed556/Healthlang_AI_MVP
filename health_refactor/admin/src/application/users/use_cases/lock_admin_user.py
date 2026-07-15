"""Use-case: manually lock an Admin Panel user, cutting off their access
without deleting the account (e.g. departing staff, suspected compromise).

Distinct from the automatic lockout in login_with_email.py, which locks an
account after too many failed password attempts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from admin.src.application.users.use_cases.get_admin_user import AdminUserDetail
from admin.src.core.exceptions import ValidationError
from admin.src.domain.users.entities import AdminRole, AdminUserStatus
from admin.src.domain.users.exceptions import AdminUserNotFoundError, LastAdminError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from admin.src.domain.users.repositories import IAdminUserRepository


class LockAdminUserUseCase:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: IAdminUserRepository,
    ) -> None:
        self._session = session
        self._users = user_repository

    async def execute(self, *, user_id: UUID, acting_admin_id: UUID) -> AdminUserDetail:
        if user_id == acting_admin_id:
            raise ValidationError("You cannot lock your own admin account")

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise AdminUserNotFoundError("Admin user not found")
        if user.status == AdminUserStatus.LOCKED:
            raise ValidationError("Admin user is already locked")

        if user.role == AdminRole.SUPER_ADMIN:
            remaining = await self._users.count_by_role(AdminRole.SUPER_ADMIN)
            if remaining <= 1:
                raise LastAdminError("Cannot lock the last Super Admin")

        user.status = AdminUserStatus.LOCKED
        user.updated_at = datetime.now(timezone.utc)
        saved = await self._users.save(user)
        await self._session.commit()

        return AdminUserDetail(
            id=saved.id,
            email=saved.email,
            first_name=saved.first_name,
            last_name=saved.last_name,
            role=saved.role,
            status=saved.status,
            google_linked=saved.google_linked,
            must_change_password=saved.must_change_password,
            failed_attempts=saved.failed_attempts,
            invited_by=saved.invited_by,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        )
