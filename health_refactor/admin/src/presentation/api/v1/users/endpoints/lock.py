"""Endpoint: manually lock an Admin Panel user (Super Admin only)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from admin.src.application.auth.dependencies import require_admin
from admin.src.application.users.dependencies import get_lock_admin_user_use_case
from admin.src.application.users.use_cases.lock_admin_user import (
    LockAdminUserUseCase,
)
from admin.src.domain.users.entities import AdminUser
from admin.src.presentation.api.v1.users.schemas import AdminUserDetailResponse

router = APIRouter()


@router.post(
    "/{user_id}/lock",
    response_model=AdminUserDetailResponse,
    summary="Lock an Admin Panel user",
    description=(
        "Super Admin only. Manually cuts off an account's access without "
        "deleting it — distinct from the automatic lock triggered by too many "
        "failed login attempts. Cannot lock your own account or the last "
        "remaining Super Admin."
    ),
    responses={
        401: {"description": "Missing or invalid admin Bearer token."},
        403: {"description": "Caller is not a Super Admin."},
        404: {"description": "Admin user not found."},
        409: {"description": "Would lock the last Super Admin."},
        422: {"description": "Admin user is already locked, or attempted self-lock."},
    },
)
async def lock_admin_user(
    user_id: UUID,
    use_case: LockAdminUserUseCase = Depends(get_lock_admin_user_use_case),
    caller: AdminUser = Depends(require_admin),
) -> AdminUserDetailResponse:
    detail = await use_case.execute(user_id=user_id, acting_admin_id=caller.id)
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
