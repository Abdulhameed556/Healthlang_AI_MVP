"""Endpoint: exchange refresh token for new access token."""
from fastapi import APIRouter, Depends, status

from backend.src.application.auth.commands.refresh_token import RefreshTokenCommand
from backend.src.application.auth.dependencies import get_refresh_token
from backend.src.application.auth.use_cases.refresh_token import RefreshToken
from backend.src.presentation.api.v1.auth.schemas import RefreshTokenRequest, RefreshTokenResponse
from backend.src.presentation.openapi import ERROR_UNAUTHORIZED, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/refresh",
    summary="Refresh access token",
    description=(
        "Exchange a valid refresh token for a new access token and rotated refresh token. "
        "Public route — no Bearer header required."
    ),
    response_model=ApiResponse[RefreshTokenResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        RefreshTokenResponse,
        success_message="Token refreshed successfully",
        errors=(*ERROR_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
    ),
)
async def refresh_token(
    body: RefreshTokenRequest,
    use_case: RefreshToken = Depends(get_refresh_token),
) -> ApiResponse[RefreshTokenResponse]:
    result = await use_case.execute(RefreshTokenCommand(refresh_token=body.refresh_token))
    return success(
        RefreshTokenResponse.model_validate(result),
        message="Token refreshed successfully",
        status_code=status.HTTP_200_OK,
    )
