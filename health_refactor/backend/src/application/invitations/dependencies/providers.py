"""FastAPI providers for invitation use-cases."""
from fastapi import Depends

from backend.src.application.invitations.use_cases.decline_invitation import DeclineInvitation
from backend.src.domain.invitations.repositories import IInvitationRepository
from backend.src.domain.users.repositories import IUserRepository
from backend.src.infrastructure.database.dependencies import (
    get_invitation_repository,
    get_user_repository,
)


def get_decline_invitation(
    invitation_repository: IInvitationRepository = Depends(get_invitation_repository),
    user_repository: IUserRepository = Depends(get_user_repository),
) -> DeclineInvitation:
    return DeclineInvitation(
        invitation_repository=invitation_repository,
        user_repository=user_repository,
    )
