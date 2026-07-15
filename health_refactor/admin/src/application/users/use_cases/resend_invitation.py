"""Use-case: resend an Admin Panel invitation with a fresh token."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from admin.src.application.users.services import (
    build_invitation_link,
    generate_invitation_token,
)
from admin.src.application.users.use_cases.invite_admin_user import (
    InviteAdminUserResult,
)
from admin.src.core.config import settings
from admin.src.core.exceptions import ValidationError
from admin.src.domain.auth.entities import AdminInvitation
from admin.src.domain.auth.value_objects import AdminInvitationStatus
from admin.src.domain.users.entities import AdminUserStatus
from admin.src.domain.users.exceptions import AdminUserNotFoundError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from admin.src.domain.auth.repositories import IAdminInvitationRepository
    from admin.src.domain.users.repositories import IAdminUserRepository
    from admin.src.infrastructure.email.client import EmailClient


class ResendInvitationUseCase:
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

    async def execute(self, *, user_id: UUID, invited_by: UUID) -> InviteAdminUserResult:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise AdminUserNotFoundError("Admin user not found")
        if user.status != AdminUserStatus.PENDING:
            raise ValidationError("Admin user does not have a pending invitation")

        pending = await self._invitations.get_by_email(user.email)
        if pending is not None:
            await self._invitations.revoke(pending.id)

        now = datetime.now(timezone.utc)
        token = generate_invitation_token()
        invitation = await self._invitations.save(
            AdminInvitation(
                id=uuid4(),
                email=user.email,
                role=user.role.value,
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
        await self._email.send_invite_email(user.email, invitation_link, user.role.value)

        return InviteAdminUserResult(
            user_id=user.id,
            invitation_id=invitation.id,
            email=user.email,
            role=user.role,
            invitation_link=invitation_link,
        )
