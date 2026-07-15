"""Endpoint: get one Admin Panel user's full profile."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends

from admin.src.application.auth.dependencies import require_any_role
from admin.src.application.users.dependencies import get_get_admin_user_use_case
from admin.src.application.users.use_cases.get_admin_user import GetAdminUserUseCase
from admin.src.domain.users.entities import AdminUser
from admin.src.presentation.api.v1.users.schemas import AdminUserDetailResponse

router = APIRouter()


@router.get(
    "/{user_id}",
    response_model=AdminUserDetailResponse,
    summary="Get an Admin Panel user's profile",
    description="Any authenticated admin (Super Admin or Read-Only) may view a user's profile.",
    responses={
        401: {"description": "Missing or invalid admin Bearer token."},
        404: {"description": "Admin user not found."},
    },
)
async def get_admin_user(
    user_id: UUID,
    use_case: GetAdminUserUseCase = Depends(get_get_admin_user_use_case),
    _: AdminUser = Depends(require_any_role),
) -> AdminUserDetailResponse:
    detail = await use_case.execute(user_id)
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
