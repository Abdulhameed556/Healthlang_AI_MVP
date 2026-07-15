"""Endpoint: unlock a locked-out Admin Panel user (Super Admin only)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from admin.src.application.auth.dependencies import require_admin
from admin.src.application.users.dependencies import get_unlock_admin_user_use_case
from admin.src.application.users.use_cases.unlock_admin_user import (
    UnlockAdminUserUseCase,
)
from admin.src.domain.users.entities import AdminUser
from admin.src.presentation.api.v1.users.schemas import AdminUserDetailResponse

router = APIRouter()


@router.post(
    "/{user_id}/unlock",
    response_model=AdminUserDetailResponse,
    summary="Unlock an Admin Panel user",
    description=(
        "Super Admin only. Resets the failed-login counter and reactivates "
        "an account that was locked out."
    ),
    responses={
        401: {"description": "Missing or invalid admin Bearer token."},
        403: {"description": "Caller is not a Super Admin."},
        404: {"description": "Admin user not found."},
        422: {"description": "Admin user is not currently locked."},
    },
)
async def unlock_admin_user(
    user_id: UUID,
    use_case: UnlockAdminUserUseCase = Depends(get_unlock_admin_user_use_case),
    _: AdminUser = Depends(require_admin),
) -> AdminUserDetailResponse:
    detail = await use_case.execute(user_id=user_id)
    return AdminUserDetailResponse(
        id=detail.id,
        email=detail.email,
        first_name=detail.first_name,
        last_name=detail.last_name,
        role=detail.role,
        status=detail.status,
        google_linked=detail.google_linked,
        must_change_password=detail.must_change_password,
        failed_attempts=detail.failed_attempts,
        invited_by=detail.invited_by,
        created_at=detail.created_at,
        updated_at=detail.updated_at,
    )
