"""Endpoint: change an Admin Panel user's role (Super Admin only)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from admin.src.application.auth.dependencies import require_admin
from admin.src.application.users.dependencies import get_edit_admin_user_role_use_case
from admin.src.application.users.use_cases.edit_admin_user_role import (
    EditAdminUserRoleUseCase,
)
from admin.src.domain.users.entities import AdminUser
from admin.src.presentation.api.v1.users.schemas import (
    AdminUserDetailResponse,
    EditAdminUserRoleRequest,
)

router = APIRouter()


@router.patch(
    "/{user_id}/role",
    response_model=AdminUserDetailResponse,
    summary="Change an Admin Panel user's role",
    description=(
        "Super Admin only. Cannot demote the last remaining Super Admin."
    ),
    responses={
        401: {"description": "Missing or invalid admin Bearer token."},
        403: {"description": "Caller is not a Super Admin."},
        404: {"description": "Admin user not found."},
        409: {"description": "Would demote the last Super Admin."},
    },
)
async def edit_admin_user_role(
    user_id: UUID,
    body: EditAdminUserRoleRequest,
    use_case: EditAdminUserRoleUseCase = Depends(get_edit_admin_user_role_use_case),
    _: AdminUser = Depends(require_admin),
) -> AdminUserDetailResponse:
    detail = await use_case.execute(user_id=user_id, new_role=body.role)
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
