"""Use-case: accept an Admin Panel invitation and set a password.

Only activates the account — the new admin still logs in afterward through
the normal two-step (password + OTP) login flow, same as everyone else.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from admin.src.core.exceptions import ConflictError, InviteExpiredError
from admin.src.core.security import hash_password
from admin.src.domain.auth.exceptions import AdminInvitationNotFoundError
from admin.src.domain.auth.value_objects import AdminInvitationStatus
from admin.src.domain.users.entities import AdminUserStatus
from admin.src.domain.users.exceptions import AdminUserNotFoundError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from admin.src.domain.auth.repositories import IAdminInvitationRepository
    from admin.src.domain.users.repositories import IAdminUserRepository


class AcceptInvitationUseCase:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: IAdminUserRepository,
        invitation_repository: IAdminInvitationRepository,
    ) -> None:
        self._session = session
        self._users = user_repository
        self._invitations = invitation_repository

    async def execute(self, *, token: str, password: str) -> str:
        invitation = await self._invitations.get_by_token(token)
        if invitation is None:
            raise AdminInvitationNotFoundError("Invitation not found")
        if invitation.status != AdminInvitationStatus.PENDING:
            raise ConflictError("Invitation has already been used")
        if invitation.expires_at <= datetime.now(timezone.utc):
            raise InviteExpiredError("Invitation has expired")

        user = await self._users.get_by_email(invitation.email)
        if user is None:
            raise AdminUserNotFoundError("Admin user not found")

        now = datetime.now(timezone.utc)
        user.password_hash = hash_password(password)
        user.status = AdminUserStatus.ACTIVE
        user.updated_at = now
        await self._users.save(user)

        await self._invitations.save(
            replace(
                invitation,
                status=AdminInvitationStatus.ACCEPTED,
                accepted_at=now,
            )
        )
        await self._session.commit()

        return user.email
