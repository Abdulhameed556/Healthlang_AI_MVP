"""Use-case: Invite a product-dashboard user via direct Python call.

In the monorepo, the Admin Panel calls the backend use-case directly instead
of going over HTTP. No BackendClient or X-Admin-Api-Key needed.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from backend.src.application.users.commands.admin import CreateInvitedUserFromAdminCommand
from backend.src.application.users.results.admin import CreateInvitedUserFromAdminResult

if TYPE_CHECKING:
    from backend.src.application.users.use_cases.create_invited_user_from_admin import (
        CreateInvitedUserFromAdmin,
    )


class InviteProductUserUseCase:
    def __init__(self, create_invited_user: CreateInvitedUserFromAdmin) -> None:
        self._create_invited_user = create_invited_user

    async def execute(
        self,
        email: str,
        department_name: str,
        first_name: str,
        last_name: str,
        description: str | None = None,
    ) -> CreateInvitedUserFromAdminResult:
        command = CreateInvitedUserFromAdminCommand(
            email=email,
            department_name=department_name,
            first_name=first_name,
            last_name=last_name,
            description=description,
        )
        return await self._create_invited_user.execute(command)
