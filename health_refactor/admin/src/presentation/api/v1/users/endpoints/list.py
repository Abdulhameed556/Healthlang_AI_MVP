"""Endpoint: list all Admin Panel users."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from admin.src.application.auth.dependencies import require_any_role
from admin.src.application.users.dependencies import get_list_admin_users_use_case
from admin.src.application.users.use_cases.list_admin_users import (
    ListAdminUsersUseCase,
)
from admin.src.domain.users.entities import AdminUser
from admin.src.presentation.api.v1.users.schemas import (
    AdminUserListResponse,
    AdminUserSummaryResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=AdminUserListResponse,
    summary="List all Admin Panel users",
    description="Any authenticated admin (Super Admin or Read-Only) may list users.",
    responses={401: {"description": "Missing or invalid admin Bearer token."}},
)
async def list_admin_users(
    use_case: ListAdminUsersUseCase = Depends(get_list_admin_users_use_case),
    _: AdminUser = Depends(require_any_role),
) -> AdminUserListResponse:
    users = await use_case.execute()
    return AdminUserListResponse(
        users=[
            AdminUserSummaryResponse(
                id=u.id,
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
                role=u.role,
                status=u.status,
                created_at=u.created_at,
            )
            for u in users
        ],
        total=len(users),
    )
