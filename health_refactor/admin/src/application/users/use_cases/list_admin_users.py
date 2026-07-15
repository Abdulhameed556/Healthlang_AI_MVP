"""Use-case: list all Admin Panel users."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from admin.src.domain.users.entities import AdminRole, AdminUserStatus
from admin.src.domain.users.repositories import IAdminUserRepository


@dataclass
class AdminUserSummary:
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: AdminRole
    status: AdminUserStatus
    created_at: datetime


class ListAdminUsersUseCase:
    def __init__(self, user_repository: IAdminUserRepository) -> None:
        self._users = user_repository

    async def execute(self) -> list[AdminUserSummary]:
        users = await self._users.list_all()
        return [
            AdminUserSummary(
                id=u.id,
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
                role=u.role,
                status=u.status,
                created_at=u.created_at,
            )
            for u in sorted(users, key=lambda u: u.created_at, reverse=True)
        ]
