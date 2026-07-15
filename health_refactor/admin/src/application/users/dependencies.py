"""FastAPI DI providers for users use-cases."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from admin.src.application.users.use_cases.edit_admin_user_role import (
    EditAdminUserRoleUseCase,
)
from admin.src.application.users.use_cases.get_admin_user import GetAdminUserUseCase
from admin.src.application.users.use_cases.invite_admin_user import (
    InviteAdminUserUseCase,
)
from admin.src.application.users.use_cases.lock_admin_user import (
    LockAdminUserUseCase,
)
from admin.src.application.users.use_cases.list_admin_users import (
    ListAdminUsersUseCase,
)
from admin.src.application.users.use_cases.remove_admin_user import (
    RemoveAdminUserUseCase,
)
from admin.src.application.users.use_cases.resend_invitation import (
    ResendInvitationUseCase,
)
from admin.src.application.users.use_cases.unlock_admin_user import (
    UnlockAdminUserUseCase,
)
from admin.src.infrastructure.database.dependencies import get_db
from admin.src.infrastructure.email.client import EmailClient
from admin.src.infrastructure.repositories.admin_invitations import (
    AdminInvitationRepository,
)
from admin.src.infrastructure.repositories.admin_users import AdminUserRepository


def get_list_admin_users_use_case(
    db: AsyncSession = Depends(get_db),
) -> ListAdminUsersUseCase:
    return ListAdminUsersUseCase(user_repository=AdminUserRepository(db))


def get_get_admin_user_use_case(
    db: AsyncSession = Depends(get_db),
) -> GetAdminUserUseCase:
    return GetAdminUserUseCase(user_repository=AdminUserRepository(db))


def get_invite_admin_user_use_case(
    db: AsyncSession = Depends(get_db),
) -> InviteAdminUserUseCase:
    return InviteAdminUserUseCase(
        session=db,
        user_repository=AdminUserRepository(db),
        invitation_repository=AdminInvitationRepository(db),
        email_client=EmailClient(),
    )


def get_edit_admin_user_role_use_case(
    db: AsyncSession = Depends(get_db),
) -> EditAdminUserRoleUseCase:
    return EditAdminUserRoleUseCase(session=db, user_repository=AdminUserRepository(db))


def get_remove_admin_user_use_case(
    db: AsyncSession = Depends(get_db),
) -> RemoveAdminUserUseCase:
    return RemoveAdminUserUseCase(session=db, user_repository=AdminUserRepository(db))


def get_unlock_admin_user_use_case(
    db: AsyncSession = Depends(get_db),
) -> UnlockAdminUserUseCase:
    return UnlockAdminUserUseCase(session=db, user_repository=AdminUserRepository(db))


def get_lock_admin_user_use_case(
    db: AsyncSession = Depends(get_db),
) -> LockAdminUserUseCase:
    return LockAdminUserUseCase(session=db, user_repository=AdminUserRepository(db))


def get_resend_invitation_use_case(
    db: AsyncSession = Depends(get_db),
) -> ResendInvitationUseCase:
    return ResendInvitationUseCase(
        session=db,
        user_repository=AdminUserRepository(db),
        invitation_repository=AdminInvitationRepository(db),
        email_client=EmailClient(),
    )
