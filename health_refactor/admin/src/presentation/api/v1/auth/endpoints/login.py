"""Endpoints: admin login (two-step email/password + OTP)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from admin.src.application.auth.dependencies import get_login_use_case
from admin.src.application.auth.use_cases.login_with_email import (
    LoginWithEmailUseCase,
)
from admin.src.presentation.api.v1.auth.schemas import (
    LoginInitiateRequest,
    LoginInitiateResponse,
    LoginVerifyRequest,
    LoginVerifyResponse,
)

router = APIRouter()


@router.post(
    "/login/initiate",
    response_model=LoginInitiateResponse,
    summary="Admin login — step 1 (request OTP)",
    description=(
        "Validates the admin's email + password and, on success, emails a "
        "6-digit one-time code. Always returns 200 with a generic message so it "
        "cannot be used to probe which emails exist. Complete login with "
        "`/auth/login/verify`."
    ),
    responses={
        401: {"description": "Invalid email or password."},
        422: {"description": "Validation error (missing/invalid fields)."},
        423: {"description": "Account locked after too many failed attempts."},
    },
)
async def login_initiate(
    body: LoginInitiateRequest,
    use_case: LoginWithEmailUseCase = Depends(get_login_use_case),
) -> LoginInitiateResponse:
    await use_case.initiate(body.email, body.password)
    return LoginInitiateResponse(message="OTP sent to your email")


@router.post(
    "/login/verify",
    response_model=LoginVerifyResponse,
    summary="Admin login — step 2 (verify OTP)",
    description=(
        "Exchanges the email + 6-digit OTP for an admin access token "
        "(60-minute session, no refresh token)."
    ),
    responses={
        401: {"description": "Invalid or expired OTP."},
        422: {"description": "Validation error (missing/invalid fields)."},
    },
)
async def login_verify(
    body: LoginVerifyRequest,
    use_case: LoginWithEmailUseCase = Depends(get_login_use_case),
) -> LoginVerifyResponse:
    token, must_change_password = await use_case.verify(body.email, body.otp)
    return LoginVerifyResponse(
        access_token=token,
        must_change_password=must_change_password,
    )
