"""SQLAlchemy implementation of IInvitationRepository."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.repositories import IInvitationRepository
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.infrastructure.database.models.invitation import Invitation as InvitationModel
from backend.src.infrastructure.repositories._mappers import invitation_to_entity, invitation_to_model
from backend.src.infrastructure.repositories._utils import normalize_email


class SqlAlchemyInvitationRepository(IInvitationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, invitation: Invitation) -> Invitation:
        model = invitation_to_model(invitation)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return invitation_to_entity(model)

    async def get_by_id(self, invitation_id: UUID) -> Invitation | None:
        result = await self._session.execute(
            select(InvitationModel).where(InvitationModel.id == invitation_id)
        )
        model = result.scalar_one_or_none()
        return invitation_to_entity(model) if model is not None else None

    async def get_by_token(self, token: str) -> Invitation | None:
        result = await self._session.execute(
            select(InvitationModel).where(InvitationModel.token == token)
        )
        model = result.scalar_one_or_none()
        return invitation_to_entity(model) if model is not None else None

    async def get_pending_by_email(self, email: str) -> Invitation | None:
        normalized = normalize_email(email)
        result = await self._session.execute(
            select(InvitationModel).where(
                InvitationModel.email == normalized,
                InvitationModel.status == InvitationStatus.PENDING,
            )
        )
        model = result.scalar_one_or_none()
        return invitation_to_entity(model) if model is not None else None

    async def get_pending_by_email_and_department(
        self, email: str, department_id: UUID
    ) -> Invitation | None:
        normalized = normalize_email(email)
        result = await self._session.execute(
            select(InvitationModel).where(
                InvitationModel.email == normalized,
                InvitationModel.department_id == department_id,
                InvitationModel.status == InvitationStatus.PENDING,
            )
        )
        model = result.scalar_one_or_none()
        return invitation_to_entity(model) if model is not None else None

    async def save(self, invitation: Invitation) -> Invitation:
        model = invitation_to_model(invitation)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)
        return invitation_to_entity(merged)
