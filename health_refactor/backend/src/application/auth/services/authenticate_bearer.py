"""Resolve a Bearer JWT to an authenticated product user."""
from datetime import datetime, timezone
from uuid import UUID

from jose import JWTError

from backend.src.application.auth.context import AuthContext
from backend.src.core.exceptions import ForbiddenError, UnauthorizedError
from backend.src.core.security import decode_token
from backend.src.domain.auth.repositories import IUserSessionRepository
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserRole, UserStatus

_NO_ORG_ACCESS_MESSAGE = "You do not have access to this department"


def _auth_context_from_user(user: User) -> AuthContext:
    return AuthContext(
        user_id=user.id,
        department_id=user.department_id,
        email=user.email,
        role=UserRole(user.role),
    )


async def _resolve_context_user(
    session_user: User,
    *,
    department_id: UUID | None,
    user_repository: IUserRepository,
) -> User:
    if department_id is None or department_id == session_user.department_id:
        return session_user

    member = await user_repository.get_by_email_and_department(
        session_user.email, department_id
    )
    if member is None or UserStatus(member.status) != UserStatus.ACTIVE:
        raise ForbiddenError(_NO_ORG_ACCESS_MESSAGE)
    return member


async def authenticate_bearer_token(
    token: str,
    *,
    user_repository: IUserRepository,
    session_repository: IUserSessionRepository,
    department_id: UUID | None = None,
) -> AuthContext:
    """Validate JWT + session and return ``AuthContext`` for the active department.

    ``AuthContext`` is unchanged: ``user_id``, ``department_id``, ``email``, ``role``.
    The optional ``department_id`` argument (from ``X-Department-Id``) only selects
    which membership row populates those fields. Endpoints keep using
    ``auth.department_id`` as today; no handler changes are required.
    """
    raw = token.strip()
    if not raw:
        raise UnauthorizedError("Missing or invalid access token")

    try:
        payload = decode_token(raw)
    except JWTError as exc:
        raise UnauthorizedError("Missing or invalid access token") from exc

    subject = payload.get("sub")
    if not subject:
        raise UnauthorizedError("Missing or invalid access token")

    try:
        user_id = UUID(str(subject))
    except ValueError as exc:
        raise UnauthorizedError("Missing or invalid access token") from exc

    session = await session_repository.get_by_token(raw)
    if session is None:
        raise UnauthorizedError("Missing or invalid access token")

    now = datetime.now(timezone.utc)
    if session.expires_at <= now:
        raise UnauthorizedError("Access token has expired")

    if session.user_id != user_id:
        raise UnauthorizedError("Missing or invalid access token")

    user = await user_repository.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("Missing or invalid access token")

    if user.status != UserStatus.ACTIVE:
        raise ForbiddenError("Account is not active")

    context_user = await _resolve_context_user(
        user,
        department_id=department_id,
        user_repository=user_repository,
    )
    return _auth_context_from_user(context_user)
