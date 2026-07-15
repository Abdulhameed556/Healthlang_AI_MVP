"""FastAPI DI providers for auth use-cases and the current-admin guard."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from admin.src.application.auth.use_cases.accept_invitation import (
    AcceptInvitationUseCase,
)
from admin.src.application.auth.use_cases.login_with_email import LoginWithEmailUseCase
from admin.src.application.auth.use_cases.logout import LogoutUseCase
from admin.src.core.exceptions import ForbiddenError, UnauthorizedError
from admin.src.core.security import decode_token, hash_token
from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus
from admin.src.infrastructure.database.dependencies import get_db
from admin.src.infrastructure.database.otp_store import OTPStore
from admin.src.infrastructure.email.client import EmailClient
from admin.src.infrastructure.repositories.admin_invitations import (
    AdminInvitationRepository,
)
from admin.src.infrastructure.repositories.admin_sessions import AdminSessionRepository
from admin.src.infrastructure.repositories.admin_users import AdminUserRepository


def get_login_use_case(
    db: AsyncSession = Depends(get_db),
) -> LoginWithEmailUseCase:
    return LoginWithEmailUseCase(
        session=db,
        user_repo=AdminUserRepository(db),
        session_repo=AdminSessionRepository(db),
        otp_store=OTPStore(db),
        email_client=EmailClient(),
    )


def get_logout_use_case(
    db: AsyncSession = Depends(get_db),
) -> LogoutUseCase:
    return LogoutUseCase(session=db, session_repo=AdminSessionRepository(db))


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or invalid Authorization header")
    return authorization.split(" ", 1)[1].strip()


async def get_current_admin(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """Validate the bearer JWT *and* its server-side session row."""
    token = _bearer_token(authorization)
    payload = decode_token(token)  # raises UnauthorizedError on bad sig/expiry

    sessions = AdminSessionRepository(db)
    session = await sessions.get_by_token(hash_token(token))
    if session is None or session.invalidated_at is not None:
        raise UnauthorizedError("Session is no longer valid")
    if session.expires_at <= datetime.now(timezone.utc):
        raise UnauthorizedError("Session has expired")

    subject = payload.get("sub")
    if not subject:
        raise UnauthorizedError("Invalid token")
    user = await AdminUserRepository(db).get_by_id(UUID(subject))
    if user is None or user.status != AdminUserStatus.ACTIVE:
        raise UnauthorizedError("Account is not active")
    return user


def require_admin(
    current: AdminUser = Depends(get_current_admin),
) -> AdminUser:
    """Allow only full Super Admins through; Read-Only callers get 403."""
    if current.role != AdminRole.SUPER_ADMIN:
        raise ForbiddenError("Super Admin role required")
    return current


def require_any_role(
    current: AdminUser = Depends(get_current_admin),
) -> AdminUser:
    """Allow any authenticated, active admin through — Super Admin or Read-Only."""
    return current


def get_accept_invitation_use_case(
    db: AsyncSession = Depends(get_db),
) -> AcceptInvitationUseCase:
    return AcceptInvitationUseCase(
        session=db,
        user_repository=AdminUserRepository(db),
        invitation_repository=AdminInvitationRepository(db),
    )
