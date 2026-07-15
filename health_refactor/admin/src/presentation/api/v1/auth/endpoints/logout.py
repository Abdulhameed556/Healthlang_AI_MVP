"""Endpoint: admin logout (invalidates the current session)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from admin.src.application.auth.dependencies import (
    get_current_admin,
    get_logout_use_case,
)
from admin.src.application.auth.use_cases.logout import LogoutUseCase
from admin.src.domain.users.entities import AdminUser
from admin.src.presentation.api.v1.auth.schemas import LogoutResponse

router = APIRouter()


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Admin logout",
    description=(
        "Invalidates the current admin session so the access token can no longer "
        "be used, even before it expires. Requires a valid admin Bearer token."
    ),
    responses={401: {"description": "Missing or invalid admin Bearer token."}},
)
async def logout(
    authorization: str = Header(default=""),
    _: AdminUser = Depends(get_current_admin),
    use_case: LogoutUseCase = Depends(get_logout_use_case),
) -> LogoutResponse:
    # get_current_admin has already validated the header shape and token.
    token = authorization.split(" ", 1)[1].strip()
    await use_case.execute(token)
    return LogoutResponse(message="Logged out")
