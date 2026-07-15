"""Endpoints: Google OAuth authorization URL and login."""
from fastapi import APIRouter, Depends, status

from backend.src.application.auth.commands.google_login import LoginWithGoogleCommand
from backend.src.application.auth.dependencies import (
    get_google_oauth_url_use_case,
    get_login_with_google,
)
from backend.src.application.auth.use_cases.get_google_oauth_url import GetGoogleOAuthUrl
from backend.src.application.auth.use_cases.login_with_google import LoginWithGoogle
from backend.src.presentation.api.v1.auth.schemas import (
    GoogleLoginRequest,
    GoogleOAuthUrlResponse,
    LoginResponse,
)
from backend.src.presentation.openapi import envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/google/url",
    summary="Get Google OAuth authorization URL",
    description=(
        "Returns the Google OAuth URL for the product SPA to redirect the user. "
        "Requires ``GOOGLE_CLIENT_ID``, ``GOOGLE_CLIENT_SECRET``, and ``GOOGLE_REDIRECT_URI``."
    ),
    response_model=ApiResponse[GoogleOAuthUrlResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        GoogleOAuthUrlResponse,
        success_message="OAuth URL ready",
        errors=(),
    ),
)
async def get_google_oauth_url(
    use_case: GetGoogleOAuthUrl = Depends(get_google_oauth_url_use_case),
) -> ApiResponse[GoogleOAuthUrlResponse]:
    result = use_case.execute()
    return success(
        GoogleOAuthUrlResponse(oauth_url=result.oauth_url),
        message="OAuth URL ready",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/google",
    summary="Login with Google OAuth",
    description=(
        "Exchange a Google authorization ``code`` for a JWT. "
        "Invitation activation: ``is_new=true`` with ``invitation_token``; "
        "Google email must match the invite. "
        "Normal login: ``is_new=false`` with ``code`` only (active users only)."
    ),
    response_model=ApiResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        LoginResponse,
        success_message="Login successful",
        errors=(),
    ),
)
async def login_with_google(
    body: GoogleLoginRequest,
    use_case: LoginWithGoogle = Depends(get_login_with_google),
) -> ApiResponse[LoginResponse]:
    result = await use_case.execute(
        LoginWithGoogleCommand(
            code=body.code,
            is_new=body.is_new,
            invitation_token=body.invitation_token,
        )
    )
    return success(
        LoginResponse.model_validate(result),
        message="Login successful",
        status_code=status.HTTP_200_OK,
    )
