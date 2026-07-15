"""Endpoint: accept an Admin Panel invitation and set a password."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from admin.src.application.auth.dependencies import get_accept_invitation_use_case
from admin.src.application.auth.use_cases.accept_invitation import (
    AcceptInvitationUseCase,
)
from admin.src.presentation.api.v1.users.schemas import (
    AcceptInvitationRequest,
    AcceptInvitationResponse,
)

router = APIRouter()


@router.post(
    "/accept-invitation",
    response_model=AcceptInvitationResponse,
    summary="Accept an Admin Panel invitation",
    description=(
        "Public — no Bearer token required, the invitation token itself is the "
        "credential. Sets the account's password and activates it; the new "
        "admin then logs in normally through the two-step OTP flow."
    ),
    responses={
        404: {"description": "Invitation not found."},
        409: {"description": "Invitation already used."},
        422: {"description": "Invitation expired, or password too short."},
    },
)
async def accept_invitation(
    body: AcceptInvitationRequest,
    use_case: AcceptInvitationUseCase = Depends(get_accept_invitation_use_case),
) -> AcceptInvitationResponse:
    email = await use_case.execute(token=body.token, password=body.password)
    return AcceptInvitationResponse(status="success", email=email)
