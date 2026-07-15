"""Endpoint: resend a pending Admin Panel invitation (Super Admin only)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from admin.src.application.auth.dependencies import require_admin
from admin.src.application.users.dependencies import get_resend_invitation_use_case
from admin.src.application.users.use_cases.resend_invitation import (
    ResendInvitationUseCase,
)
from admin.src.domain.users.entities import AdminUser
from admin.src.presentation.api.v1.users.schemas import InviteAdminUserResponse

router = APIRouter()


@router.post(
    "/{user_id}/resend-invitation",
    response_model=InviteAdminUserResponse,
    summary="Resend a pending invitation",
    description=(
        "Super Admin only. Revokes the previous invitation token and sends a "
        "fresh one. Only valid for users still in `pending` status."
    ),
    responses={
        401: {"description": "Missing or invalid admin Bearer token."},
        403: {"description": "Caller is not a Super Admin."},
        404: {"description": "Admin user not found."},
        422: {"description": "Admin user does not have a pending invitation."},
    },
)
async def resend_invitation(
    user_id: UUID,
    use_case: ResendInvitationUseCase = Depends(get_resend_invitation_use_case),
    caller: AdminUser = Depends(require_admin),
) -> InviteAdminUserResponse:
    result = await use_case.execute(user_id=user_id, invited_by=caller.id)
    return InviteAdminUserResponse(
        user_id=result.user_id,
        invitation_id=result.invitation_id,
        email=result.email,
        role=result.role,
        invitation_link=result.invitation_link,
    )
