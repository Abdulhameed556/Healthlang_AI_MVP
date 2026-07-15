"""Endpoint: invite a product-dashboard user (Admin-only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from admin.src.application.auth.dependencies import require_admin
from admin.src.application.departments.dependencies import (
    get_invite_product_user_use_case,
)
from admin.src.application.departments.use_cases.invite_product_user import (
    InviteProductUserUseCase,
)
from admin.src.domain.users.entities import AdminUser
from admin.src.presentation.api.v1.departments.schemas import (
    InviteProductUserRequest,
    InviteProductUserResponse,
)

router = APIRouter()


@router.post(
    "/invitations",
    response_model=InviteProductUserResponse,
    status_code=201,
    summary="Invite a hospital department + super-admin",
    description=(
        "Admin-only. Provisions a new hospital department and its super-admin "
        "user (status `INVITED`) via a direct in-process call into the backend "
        "service, then returns the invitation link. Requires the `admin` role; "
        "`read_only` is rejected."
    ),
    responses={
        401: {"description": "Missing or invalid admin Bearer token."},
        403: {"description": "Caller is not an admin (read_only)."},
        409: {"description": "A user with this email already exists."},
        422: {"description": "Validation error (missing/invalid fields)."},
    },
)
async def invite_product_user(
    body: InviteProductUserRequest,
    use_case: InviteProductUserUseCase = Depends(
        get_invite_product_user_use_case
    ),
    _: AdminUser = Depends(require_admin),
) -> InviteProductUserResponse:
    result = await use_case.execute(
        email=body.email,
        department_name=body.department_name,
        first_name=body.first_name,
        last_name=body.last_name,
        description=body.description,
    )
    return InviteProductUserResponse(
        status="success",
        email=body.email,
        invitation_link=result.invitation_link,
    )
