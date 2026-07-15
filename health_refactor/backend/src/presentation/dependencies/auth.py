"""Product user JWT authentication dependencies."""
from collections.abc import Callable

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.src.application.auth.context import AuthContext
from backend.src.application.auth.services.authenticate_bearer import authenticate_bearer_token
from backend.src.core.exceptions import ForbiddenError, UnauthorizedError
from backend.src.domain.auth.repositories import IUserSessionRepository
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.value_objects import UserRole
from backend.src.infrastructure.database.dependencies import (
    get_user_repository,
    get_user_session_repository,
)
from backend.src.presentation.dependencies.department_context import (
    DEPARTMENT_ID_HEADER,
    parse_department_id_header,
)

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Product user JWT from login or Google OAuth.",
)


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    department_id_header: str | None = Header(
        None,
        alias=DEPARTMENT_ID_HEADER,
        description=(
            "Active department for this request. When omitted, the department "
            "from the login session is used."
        ),
    ),
    user_repository: IUserRepository = Depends(get_user_repository),
    session_repository: IUserSessionRepository = Depends(get_user_session_repository),
) -> AuthContext:
    """Require a valid Bearer JWT tied to an active user session."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing or invalid access token")

    return await authenticate_bearer_token(
        credentials.credentials,
        user_repository=user_repository,
        session_repository=session_repository,
        department_id=parse_department_id_header(department_id_header),
    )


def require_roles(*allowed_roles: UserRole) -> Callable[..., AuthContext]:
    """Factory: restrict a route to one or more product user roles."""

    async def _require_roles(
        auth_context: AuthContext = Depends(require_auth),
    ) -> AuthContext:
        if auth_context.role not in allowed_roles:
            raise ForbiddenError("Insufficient permissions")
        return auth_context

    return _require_roles


require_org_inviter = require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)
require_front_desk = require_roles(UserRole.FRONT_DESK, UserRole.SUPER_ADMIN)
require_nurse = require_roles(UserRole.NURSE, UserRole.SUPER_ADMIN)
require_doctor = require_roles(UserRole.DOCTOR, UserRole.SUPER_ADMIN)
require_lab_scientist = require_roles(UserRole.LAB_SCIENTIST, UserRole.SUPER_ADMIN)
require_pharmacist = require_roles(UserRole.PHARMACIST, UserRole.SUPER_ADMIN)
require_doctor_or_lab_scientist = require_roles(
    UserRole.DOCTOR, UserRole.LAB_SCIENTIST, UserRole.SUPER_ADMIN
)
require_doctor_or_pharmacist = require_roles(
    UserRole.DOCTOR, UserRole.PHARMACIST, UserRole.SUPER_ADMIN
)
require_pharmacist_or_admin = require_roles(
    UserRole.PHARMACIST, UserRole.ADMIN, UserRole.SUPER_ADMIN
)
require_super_admin = require_roles(UserRole.SUPER_ADMIN)
require_clinical_staff = require_roles(
    UserRole.DOCTOR, UserRole.NURSE, UserRole.SUPER_ADMIN
)
