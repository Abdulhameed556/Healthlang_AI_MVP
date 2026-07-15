"""Endpoint handlers: password reset request and completion."""
from fastapi import APIRouter, Depends, status

from backend.src.application.auth.commands.complete_password_reset import (
    CompletePasswordResetCommand,
)
from backend.src.application.auth.commands.request_password_reset import (
    RequestPasswordResetCommand,
)
from backend.src.application.auth.dependencies import (
    get_complete_password_reset,
    get_request_password_reset,
)
from backend.src.application.auth.use_cases.complete_password_reset import (
    CompletePasswordReset,
)
from backend.src.application.auth.use_cases.request_password_reset import (
    RequestPasswordReset,
)
from backend.src.presentation.api.v1.auth.schemas import (
    CompletePasswordResetRequest,
    PasswordResetMessageResponse,
    RequestPasswordResetRequest,
    RequestPasswordResetResponse,
)
from backend.src.presentation.openapi import envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/password-reset/request",
    summary="Request password reset",
    description=(
        "Sends a password reset link to the email when an active email/password "
        "account exists. Always returns success to avoid email enumeration. "
        "In development (when email is not sent), ``data.reset_link`` contains the "
        "URL for local testing."
    ),
    response_model=ApiResponse[RequestPasswordResetResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        RequestPasswordResetResponse,
        success_message="Password reset request accepted",
        errors=(),
    ),
)
async def request_password_reset(
    body: RequestPasswordResetRequest,
    use_case: RequestPasswordReset = Depends(get_request_password_reset),
) -> ApiResponse[RequestPasswordResetResponse]:
    result = await use_case.execute(
        RequestPasswordResetCommand(email=str(body.email))
    )
    return success(
        RequestPasswordResetResponse(
            message=result.message,
            reset_link=result.reset_link,
        ),
        message="Password reset request accepted",
        status_code=status.HTTP_200_OK,
    )


@router.post(
    "/password-reset/complete",
    summary="Complete password reset",
    description=(
        "Sets a new password using the ``email`` and ``token`` from the reset link."
    ),
    response_model=ApiResponse[PasswordResetMessageResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        PasswordResetMessageResponse,
        success_message="Password reset successfully",
        errors=(status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY),
    ),
)
async def complete_password_reset(
    body: CompletePasswordResetRequest,
    use_case: CompletePasswordReset = Depends(get_complete_password_reset),
) -> ApiResponse[PasswordResetMessageResponse]:
    result = await use_case.execute(
        CompletePasswordResetCommand(
            email=str(body.email),
            token=body.token,
            new_password=body.new_password,
        )
    )
    return success(
        PasswordResetMessageResponse(message=result.message),
        message="Password reset successfully",
        status_code=status.HTTP_200_OK,
    )
