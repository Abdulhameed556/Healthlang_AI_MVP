"""Endpoint: remove an Admin Panel user (Super Admin only)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from admin.src.application.auth.dependencies import require_admin
from admin.src.application.users.dependencies import get_remove_admin_user_use_case
from admin.src.application.users.use_cases.remove_admin_user import (
    RemoveAdminUserUseCase,
)
from admin.src.domain.users.entities import AdminUser

router = APIRouter()


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an Admin Panel user",
    description=(
        "Super Admin only. Permanently deletes the admin user. Cannot remove "
        "your own account or the last remaining Super Admin."
    ),
    responses={
        401: {"description": "Missing or invalid admin Bearer token."},
        403: {"description": "Caller is not a Super Admin."},
        404: {"description": "Admin user not found."},
        409: {"description": "Would remove the last Super Admin."},
        422: {"description": "Attempted to remove your own account."},
    },
)
async def remove_admin_user(
    user_id: UUID,
    use_case: RemoveAdminUserUseCase = Depends(get_remove_admin_user_use_case),
    caller: AdminUser = Depends(require_admin),
) -> None:
    await use_case.execute(user_id=user_id, acting_admin_id=caller.id)
