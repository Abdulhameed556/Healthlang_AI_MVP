"""FastAPI providers that wire repositories into user use-case classes."""
from fastapi import Depends

from backend.src.application.users.dependencies.infrastructure import get_invitation_email_sender
from backend.src.application.users.use_cases.create_invited_user_from_admin import (
    CreateInvitedUserFromAdmin,
)
from backend.src.application.users.use_cases.get_current_user_profile import (
    GetCurrentUserProfile,
)
from backend.src.application.users.use_cases.list_user_departments import (
    ListUserDepartments,
)
from backend.src.domain.invitations.repositories import IInvitationRepository
from backend.src.domain.departments.repositories import IDepartmentRepository
from backend.src.domain.users.repositories import IUserRepository
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.infrastructure.database.dependencies import (
    get_invitation_repository,
    get_department_repository,
    get_unit_of_work,
    get_user_repository,
)


def get_current_user_profile(
    user_repository: IUserRepository = Depends(get_user_repository),
) -> GetCurrentUserProfile:
    return GetCurrentUserProfile(user_repository=user_repository)


def get_list_user_departments(
    user_repository: IUserRepository = Depends(get_user_repository),
    department_repository: IDepartmentRepository = Depends(get_department_repository),
) -> ListUserDepartments:
    return ListUserDepartments(
        user_repository=user_repository,
        department_repository=department_repository,
    )


def get_create_invited_user_from_admin(
    department_repository: IDepartmentRepository = Depends(get_department_repository),
    user_repository: IUserRepository = Depends(get_user_repository),
    invitation_repository: IInvitationRepository = Depends(get_invitation_repository),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> CreateInvitedUserFromAdmin:
    return CreateInvitedUserFromAdmin(
        department_repository=department_repository,
        user_repository=user_repository,
        invitation_repository=invitation_repository,
        invitation_email_sender=get_invitation_email_sender(),
        unit_of_work=unit_of_work,
    )
