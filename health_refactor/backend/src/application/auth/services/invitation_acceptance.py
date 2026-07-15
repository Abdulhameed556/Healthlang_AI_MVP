"""Shared invitation acceptance steps for email and Google login."""
from dataclasses import replace
from datetime import datetime
from uuid import UUID

from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.repositories import IInvitationRepository
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.departments.exceptions import DepartmentNotFoundError
from backend.src.domain.departments.repositories import IDepartmentRepository
from backend.src.domain.departments.value_objects import DepartmentStatus
from backend.src.domain.users.entities import User
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.value_objects import UserAuthMethod, UserStatus


async def mark_invitation_accepted(
    invitation_repository: IInvitationRepository,
    invitation: Invitation,
    *,
    now: datetime,
) -> None:
    accepted = replace(
        invitation,
        status=InvitationStatus.ACCEPTED,
        accepted_at=now,
    )
    await invitation_repository.save(accepted)


async def activate_department_if_invited(
    department_repository: IDepartmentRepository,
    department_id: UUID,
) -> None:
    department = await department_repository.get_by_id(department_id)
    if department is None:
        raise DepartmentNotFoundError("Department not found")
    if department.status == DepartmentStatus.INVITED:
        await department_repository.save(
            replace(department, status=DepartmentStatus.ACTIVE)
        )


async def activate_invited_user_with_password(
    user_repository: IUserRepository,
    user: User,
    password_hash: str,
    *,
    now: datetime,
) -> User:
    activated = replace(
        user,
        password_hash=password_hash,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        updated_at=now,
    )
    return await user_repository.save(activated)


async def activate_invited_user_with_google(
    user_repository: IUserRepository,
    user: User,
    *,
    given_name: str,
    family_name: str,
    now: datetime,
) -> User:
    activated = replace(
        user,
        password_hash=None,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.GOOGLE_OAUTH,
        first_name=given_name or user.first_name,
        last_name=family_name or user.last_name,
        updated_at=now,
    )
    return await user_repository.save(activated)
