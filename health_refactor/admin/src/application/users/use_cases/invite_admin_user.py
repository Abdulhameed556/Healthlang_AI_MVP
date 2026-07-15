"""Use-case: invite a new Admin Panel user (super_admin or read_only)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from admin.src.application.users.services import (
    build_invitation_link,
    generate_invitation_token,
)
from admin.src.core.config import settings
from admin.src.core.exceptions import ConflictError
from admin.src.domain.auth.entities import AdminInvitation
from admin.src.domain.auth.value_objects import AdminInvitationStatus
from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from admin.src.domain.auth.repositories import IAdminInvitationRepository
    from admin.src.domain.users.repositories import IAdminUserRepository
    from admin.src.infrastructure.email.client import EmailClient


@dataclass
class InviteAdminUserResult:
    user_id: UUID
    invitation_id: UUID
    email: str
    role: AdminRole
    invitation_link: str


class InviteAdminUserUseCase:
    def __init__(
        self,
        session: AsyncSession,
        user_repository: IAdminUserRepository,
        invitation_repository: IAdminInvitationRepository,
        email_client: EmailClient,
    ) -> None:
        self._session = session
        self._users = user_repository
        self._invitations = invitation_repository
        self._email = email_client

    async def execute(
        self,
        *,
        email: str,
        first_name: str,
        last_name: str,
        role: AdminRole,
        invited_by: UUID,
    ) -> InviteAdminUserResult:
        normalized = email.strip().lower()

        existing = await self._users.get_by_email(normalized)
        if existing is not None:
            raise ConflictError(f"An admin user with email {normalized} already exists")

        pending = await self._invitations.get_by_email(normalized)
        if pending is not None:
            await self._invitations.revoke(pending.id)

        now = datetime.now(timezone.utc)
        user = await self._users.save(
            AdminUser(
                id=uuid4(),
                email=normalized,
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                role=role,
                status=AdminUserStatus.PENDING,
                password_hash=None,
                google_linked=False,
                must_change_password=False,
                failed_attempts=0,
                invited_by=invited_by,
                created_at=now,
                updated_at=now,
            )
        )

        token = generate_invitation_token()
        invitation = await self._invitations.save(
            AdminInvitation(
                id=uuid4(),
                email=normalized,
                role=role.value,
                token=token,
                invited_by=invited_by,
                status=AdminInvitationStatus.PENDING,
                expires_at=now + timedelta(hours=settings.invitation_expire_hours),
                accepted_at=None,
                created_at=now,
            )
        )
        await self._session.commit()

        invitation_link = build_invitation_link(token=token)
        await self._email.send_invite_email(normalized, invitation_link, role.value)

        return InviteAdminUserResult(
            user_id=user.id,
            invitation_id=invitation.id,
            email=normalized,
            role=role,
            invitation_link=invitation_link,
        )
