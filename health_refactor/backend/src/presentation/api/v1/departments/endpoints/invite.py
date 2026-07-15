"""Endpoint: invite a teammate into the caller's department."""
from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.departments.commands.invite_user import InviteUserCommand
from backend.src.application.departments.dependencies import get_invite_user
from backend.src.application.departments.use_cases.invite_user import InviteUser
from backend.src.domain.users.value_objects import UserRole
from backend.src.presentation.api.v1.departments.schemas import InviteUserRequest, InviteUserResponse
from backend.src.presentation.dependencies.auth import require_org_inviter
from backend.src.presentation.openapi import envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/users/invite",
    summary="Invite department member",
    description=(
        "Creates an invited user and pending invitation in the **caller's department**, "
        "then sends the invitation email. Requires product JWT (`super_admin` or `admin`). "
        "Invitee accepts via `POST /auth/login` or `POST /auth/google` with `is_new=true`."
    ),
    response_model=ApiResponse[InviteUserResponse],
    status_code=status.HTTP_201_CREATED,
    responses=envelope_responses(
        InviteUserResponse,
        success_status=status.HTTP_201_CREATED,
        success_message="Invitation sent successfully",
        success_description="Invited user and invitation created; email queued.",
        errors=(
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_409_CONFLICT,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ),
    ),
    response_description="Standard envelope with invite details in `data`.",
)
async def invite_user(
    body: InviteUserRequest,
    auth: AuthContext = Depends(require_org_inviter),
    use_case: InviteUser = Depends(get_invite_user),
) -> ApiResponse[InviteUserResponse]:
    result = await use_case.execute(
        InviteUserCommand(
            email=str(body.email),
            role=UserRole(body.role.value),
            first_name=body.first_name,
            last_name=body.last_name,
            inviter_id=auth.user_id,
            inviter_department_id=auth.department_id,
            inviter_role=auth.role,
        )
    )
    return success(
        InviteUserResponse.model_validate(result),
        message="Invitation sent successfully",
        status_code=status.HTTP_201_CREATED,
    )
