"""Endpoint: Admin Portal provisions invited super-admin + department."""
from fastapi import APIRouter, Depends, status

from backend.src.application.users.commands import CreateInvitedUserFromAdminCommand
from backend.src.application.users.dependencies import get_create_invited_user_from_admin
from backend.src.application.users.use_cases.create_invited_user_from_admin import (
    CreateInvitedUserFromAdmin,
)
from backend.src.presentation.api.v1.internal.admin.schemas import (
    CreateInvitedUserFromAdminRequest,
    CreateInvitedUserFromAdminResponse,
)
from backend.src.presentation.openapi import ERROR_ADMIN_INTERNAL, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/users",
    summary="Provision invited super-admin",
    description=(
        "Creates a department (`invited`), super-admin user (`invited`), and pending "
        "invitation, then sends the invitation email. **Admin Portal only** — requires API key."
    ),
    response_model=ApiResponse[CreateInvitedUserFromAdminResponse],
    status_code=status.HTTP_201_CREATED,
    responses=envelope_responses(
        CreateInvitedUserFromAdminResponse,
        success_status=status.HTTP_201_CREATED,
        success_message="Invited user created successfully",
        success_description="Department, user, and invitation created; email queued.",
        errors=ERROR_ADMIN_INTERNAL,
    ),
    response_description="Standard envelope with created entities in `data`.",
)
async def create_invited_user_from_admin(
    body: CreateInvitedUserFromAdminRequest,
    use_case: CreateInvitedUserFromAdmin = Depends(get_create_invited_user_from_admin),
) -> ApiResponse[CreateInvitedUserFromAdminResponse]:
    result = await use_case.execute(
        CreateInvitedUserFromAdminCommand(
            email=str(body.email),
            department_name=body.department_name,
            first_name=body.first_name,
            last_name=body.last_name,
            description=body.description,
        )
    )
    return success(
        CreateInvitedUserFromAdminResponse.model_validate(result),
        message="Invited user created successfully",
        status_code=status.HTTP_201_CREATED,
    )
