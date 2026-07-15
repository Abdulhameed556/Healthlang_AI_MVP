"""SQLAlchemy implementation of IAdminInvitationRepository."""
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from admin.src.domain.auth.entities import AdminInvitation
from admin.src.domain.auth.value_objects import AdminInvitationStatus
from admin.src.infrastructure.database.models.admin_invitation import (
    AdminInvitation as AdminInvitationModel,
)


def _to_entity(row: AdminInvitationModel) -> AdminInvitation:
    return AdminInvitation(
        id=row.id,
        email=row.email,
        role=row.role,
        token=row.token,
        invited_by=row.invited_by,
        status=row.status,
        expires_at=row.expires_at,
        accepted_at=row.accepted_at,
        created_at=row.created_at,
    )


def _to_model(invitation: AdminInvitation) -> AdminInvitationModel:
    return AdminInvitationModel(
        id=invitation.id,
        email=invitation.email,
        role=invitation.role,
        token=invitation.token,
        invited_by=invitation.invited_by,
        status=invitation.status,
        expires_at=invitation.expires_at,
        accepted_at=invitation.accepted_at,
        created_at=invitation.created_at,
    )


class AdminInvitationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_token(self, token: str) -> AdminInvitation | None:
        result = await self._session.execute(
            select(AdminInvitationModel).where(AdminInvitationModel.token == token)
        )
        row = result.scalar_one_or_none()
        return _to_entity(row) if row else None

    async def get_by_email(self, email: str) -> AdminInvitation | None:
        """The current pending invitation for this email, if any."""
        result = await self._session.execute(
            select(AdminInvitationModel)
            .where(
                AdminInvitationModel.email == email.lower().strip(),
                AdminInvitationModel.status == AdminInvitationStatus.PENDING,
            )
            .order_by(AdminInvitationModel.created_at.desc())
        )
        row = result.scalars().first()
        return _to_entity(row) if row else None

    async def save(self, invitation: AdminInvitation) -> AdminInvitation:
        row = _to_model(invitation)
        merged = await self._session.merge(row)
        await self._session.flush()
        await self._session.refresh(merged)
        return _to_entity(merged)

    async def revoke(self, id: UUID) -> None:
        await self._session.execute(
            update(AdminInvitationModel)
            .where(AdminInvitationModel.id == id)
            .values(status=AdminInvitationStatus.REVOKED)
        )
