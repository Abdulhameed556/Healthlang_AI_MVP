"""FastAPI dependency-injection providers for departments use-cases."""
from fastapi import Depends

from backend.src.application.departments.use_cases.get_department_profile import (
    GetDepartmentProfile,
)
from backend.src.application.departments.use_cases.invite_user import InviteUser
from backend.src.application.departments.use_cases.list_department_users import (
    ListDepartmentUsers,
)
from backend.src.application.departments.use_cases.remove_department_member import (
    RemoveDepartmentMember,
)
from backend.src.application.departments.use_cases.update_department_profile import (
    UpdateDepartmentProfile,
)
from backend.src.application.departments.use_cases.update_user_role import UpdateUserRole
from backend.src.application.users.dependencies.infrastructure import get_invitation_email_sender
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.auth.repositories import IUserSessionRepository
from backend.src.domain.invitations.repositories import IInvitationRepository
from backend.src.domain.departments.repositories import IDepartmentRepository
from backend.src.domain.users.repositories import IUserRepository
from backend.src.infrastructure.database.dependencies import (
    get_invitation_repository,
    get_department_repository,
    get_unit_of_work,
    get_user_repository,
    get_user_session_repository,
)


def get_invite_user(
    department_repository: IDepartmentRepository = Depends(get_department_repository),
    user_repository: IUserRepository = Depends(get_user_repository),
    invitation_repository: IInvitationRepository = Depends(get_invitation_repository),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> InviteUser:
    return InviteUser(
        department_repository=department_repository,
        user_repository=user_repository,
        invitation_repository=invitation_repository,
        invitation_email_sender=get_invitation_email_sender(),
        unit_of_work=unit_of_work,
    )


def get_department_profile(
    department_repository: IDepartmentRepository = Depends(get_department_repository),
) -> GetDepartmentProfile:
    return GetDepartmentProfile(department_repository=department_repository)


def get_update_department_profile(
    department_repository: IDepartmentRepository = Depends(get_department_repository),
) -> UpdateDepartmentProfile:
    return UpdateDepartmentProfile(department_repository=department_repository)


def get_list_department_users(
    user_repository: IUserRepository = Depends(get_user_repository),
) -> ListDepartmentUsers:
    return ListDepartmentUsers(user_repository=user_repository)


def get_remove_department_member(
    user_repository: IUserRepository = Depends(get_user_repository),
    invitation_repository: IInvitationRepository = Depends(get_invitation_repository),
    session_repository: IUserSessionRepository = Depends(get_user_session_repository),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> RemoveDepartmentMember:
    return RemoveDepartmentMember(
        user_repository=user_repository,
        invitation_repository=invitation_repository,
        session_repository=session_repository,
        unit_of_work=unit_of_work,
    )


def get_update_user_role(
    user_repository: IUserRepository = Depends(get_user_repository),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> UpdateUserRole:
    return UpdateUserRole(
        user_repository=user_repository,
        unit_of_work=unit_of_work,
    )
