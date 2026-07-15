"""Endpoint: current authenticated admin profile."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from admin.src.application.auth.dependencies import get_current_admin
from admin.src.domain.users.entities import AdminUser
from admin.src.presentation.api.v1.users.schemas import CurrentAdminResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=CurrentAdminResponse,
    summary="Get current admin profile",
    description=(
        "Returns the authenticated admin's own profile. Requires a valid admin "
        "Bearer token. The password hash is never returned."
    ),
    responses={401: {"description": "Missing/invalid token or inactive account."}},
)
async def get_current_admin_profile(
    admin: AdminUser = Depends(get_current_admin),
) -> CurrentAdminResponse:
    return CurrentAdminResponse(
        user_id=admin.id,
        email=admin.email,
        first_name=admin.first_name,
        last_name=admin.last_name,
        role=admin.role,
        status=admin.status,
        must_change_password=admin.must_change_password,
    )
