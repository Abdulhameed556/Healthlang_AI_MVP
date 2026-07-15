"""Endpoint: email/password login (normal or invitation activation)."""
from fastapi import APIRouter, Depends, status

from backend.src.application.auth.commands.login import LoginWithEmailCommand
from backend.src.application.auth.dependencies import get_login_with_email
from backend.src.application.auth.use_cases.login_with_email import LoginWithEmail
from backend.src.presentation.api.v1.auth.schemas import LoginRequest, LoginResponse
from backend.src.presentation.openapi import envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/login",
    summary="Login with email and password",
    description=(
        "Normal login: ``is_new=false`` with ``email`` + ``password``. "
        "Invitation activation: ``is_new=true`` with ``invitation_token`` + ``password``; "
        "``email`` is optional and must match the invite when provided."
    ),
    response_model=ApiResponse[LoginResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        LoginResponse,
        success_message="Login successful",
        errors=(),
    ),
)
async def login(
    body: LoginRequest,
    use_case: LoginWithEmail = Depends(get_login_with_email),
) -> ApiResponse[LoginResponse]:
    result = await use_case.execute(
        LoginWithEmailCommand(
            password=body.password,
            is_new=body.is_new,
            email=str(body.email) if body.email else None,
            invitation_token=body.invitation_token,
        )
    )
    return success(
        LoginResponse.model_validate(result),
        message="Login successful",
        status_code=status.HTTP_200_OK,
    )
