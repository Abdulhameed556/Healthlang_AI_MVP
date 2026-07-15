"""Use-case: get one Admin Panel user's full profile."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from admin.src.domain.users.entities import AdminRole, AdminUserStatus
from admin.src.domain.users.exceptions import AdminUserNotFoundError
from admin.src.domain.users.repositories import IAdminUserRepository


@dataclass
class AdminUserDetail:
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: AdminRole
    status: AdminUserStatus
    google_linked: bool
    must_change_password: bool
    failed_attempts: int
    invited_by: UUID | None
    created_at: datetime
    updated_at: datetime


class GetAdminUserUseCase:
    def __init__(self, user_repository: IAdminUserRepository) -> None:
        self._users = user_repository

    async def execute(self, user_id: UUID) -> AdminUserDetail:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise AdminUserNotFoundError("Admin user not found")
        return AdminUserDetail(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            status=user.status,
            google_linked=user.google_linked,
            must_change_password=user.must_change_password,
            failed_attempts=user.failed_attempts,
            invited_by=user.invited_by,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
