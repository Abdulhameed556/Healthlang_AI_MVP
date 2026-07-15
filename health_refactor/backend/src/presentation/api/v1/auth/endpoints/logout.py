"""Endpoint: logout (invalidate current session)."""
from fastapi import Depends, status
from fastapi import APIRouter
from fastapi.security import HTTPAuthorizationCredentials

from backend.src.application.auth.commands.logout import LogoutCommand
from backend.src.application.auth.dependencies import get_logout
from backend.src.application.auth.use_cases.logout import Logout
from backend.src.core.exceptions import UnauthorizedError
from backend.src.presentation.dependencies.auth import bearer_scheme
from backend.src.presentation.openapi import ERROR_UNAUTHORIZED, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success
from backend.src.presentation.schemas.common import HealthData

router = APIRouter()


@router.post(
    "/logout",
    summary="Logout",
    description=(
        "Invalidates the Bearer access token's `user_sessions` row. "
        "Idempotent: calling again with the same token still returns success. "
        "Requires `Authorization: Bearer <access_token>`."
    ),
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        HealthData,
        success_message="Logout successful",
        success_description="Session invalidated; `data` is null.",
        success_example_data=None,
        errors=ERROR_UNAUTHORIZED,
    ),
)
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    use_case: Logout = Depends(get_logout),
) -> ApiResponse[None]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing or invalid access token")

    await use_case.execute(LogoutCommand(access_token=credentials.credentials))
    return success(
        None,
        message="Logout successful",
        status_code=status.HTTP_200_OK,
    )
