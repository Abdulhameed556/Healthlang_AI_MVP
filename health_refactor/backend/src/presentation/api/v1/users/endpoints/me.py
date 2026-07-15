"""Endpoint: current authenticated user profile."""
from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.users.commands.get_current_user_profile import (
    GetCurrentUserProfileCommand,
)
from backend.src.application.users.dependencies import get_current_user_profile
from backend.src.application.users.use_cases.get_current_user_profile import GetCurrentUserProfile
from backend.src.presentation.api.v1.users.schemas import CurrentUserProfileResponse
from backend.src.presentation.dependencies.auth import require_auth
from backend.src.presentation.openapi import ERROR_JWT, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/me",
    summary="Get current user profile",
    description=(
        "Returns the authenticated user's profile for the department tied to this JWT session. "
        "All roles may call this route."
    ),
    response_model=ApiResponse[CurrentUserProfileResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        CurrentUserProfileResponse,
        success_message="Profile retrieved successfully",
        errors=(*ERROR_JWT, status.HTTP_404_NOT_FOUND),
    ),
)
async def get_current_user(
    auth: AuthContext = Depends(require_auth),
    use_case: GetCurrentUserProfile = Depends(get_current_user_profile),
) -> ApiResponse[CurrentUserProfileResponse]:
    result = await use_case.execute(GetCurrentUserProfileCommand(user_id=auth.user_id))
    return success(
        CurrentUserProfileResponse.model_validate(result),
        message="Profile retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
