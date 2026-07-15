"""Endpoint: invite a new Admin Panel user (Super Admin only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from admin.src.application.auth.dependencies import require_admin
from admin.src.application.users.dependencies import get_invite_admin_user_use_case
from admin.src.application.users.use_cases.invite_admin_user import (
    InviteAdminUserUseCase,
)
from admin.src.domain.users.entities import AdminUser
from admin.src.presentation.api.v1.users.schemas import (
    InviteAdminUserRequest,
    InviteAdminUserResponse,
)

router = APIRouter()


@router.post(
    "/invite",
    response_model=InviteAdminUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a new Admin Panel user",
    description=(
        "Super Admin only. Creates a pending admin user and emails an "
        "invitation link to set their password."
    ),
    responses={
        401: {"description": "Missing or invalid admin Bearer token."},
        403: {"description": "Caller is not a Super Admin."},
        409: {"description": "An admin user with this email already exists."},
        422: {"description": "Validation error (missing/invalid fields)."},
    },
)
async def invite_admin_user(
    body: InviteAdminUserRequest,
    use_case: InviteAdminUserUseCase = Depends(get_invite_admin_user_use_case),
    caller: AdminUser = Depends(require_admin),
) -> InviteAdminUserResponse:
    result = await use_case.execute(
        email=body.email,
        first_name=body.first_name,
        last_name=body.last_name,
        role=body.role,
        invited_by=caller.id,
    )
    return InviteAdminUserResponse(
        user_id=result.user_id,
        invitation_id=result.invitation_id,
        email=result.email,
        role=result.role,
        invitation_link=result.invitation_link,
    )
