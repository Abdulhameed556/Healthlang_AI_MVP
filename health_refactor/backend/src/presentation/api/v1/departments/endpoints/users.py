"""Endpoints: department member management."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.departments.commands.list_department_users import (
    ListDepartmentUsersCommand,
)
from backend.src.application.departments.commands.remove_department_member import (
    RemoveDepartmentMemberCommand,
)
from backend.src.application.departments.commands.update_department_member_role import (
    UpdateDepartmentMemberRoleCommand,
)
from backend.src.application.departments.dependencies import (
    get_list_department_users,
    get_remove_department_member,
    get_update_user_role,
)
from backend.src.application.departments.use_cases.list_department_users import (
    ListDepartmentUsers,
)
from backend.src.application.departments.use_cases.remove_department_member import (
    RemoveDepartmentMember,
)
from backend.src.application.departments.use_cases.update_user_role import UpdateUserRole
from backend.src.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from backend.src.domain.users.value_objects import UserRole
from backend.src.presentation.api.v1.departments.schemas import (
    ListDepartmentUsersResponse,
    RemoveDepartmentMemberResponse,
    UpdateDepartmentMemberRoleRequest,
    UpdateDepartmentMemberRoleResponse,
)
from backend.src.presentation.dependencies.auth import require_org_inviter
from backend.src.presentation.openapi import ERROR_JWT, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/users",
    summary="List department members",
    description=(
        "Returns a paginated list of active and invited members of the caller's department "
        "with email and role. Use `page` and `page_size` query parameters. "
        "Requires `super_admin` or `admin`."
    ),
    response_model=ApiResponse[ListDepartmentUsersResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        ListDepartmentUsersResponse,
        success_message="Department members retrieved successfully",
        errors=ERROR_JWT,
    ),
)
async def list_department_users(
    auth: AuthContext = Depends(require_org_inviter),
    use_case: ListDepartmentUsers = Depends(get_list_department_users),
    page: int = Query(1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(
        DEFAULT_PAGE_SIZE,
        ge=1,
        le=MAX_PAGE_SIZE,
        description="Members per page.",
    ),
) -> ApiResponse[ListDepartmentUsersResponse]:
    result = await use_case.execute(
        ListDepartmentUsersCommand(
            department_id=auth.department_id,
            page=page,
            page_size=page_size,
        )
    )
    return success(
        ListDepartmentUsersResponse.model_validate(result),
        message="Department members retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.delete(
    "/users/{user_id}",
    summary="Remove department member",
    description=(
        "Suspends a member in the caller's department and invalidates their sessions. "
        "Requires `super_admin` or `admin`. Admins cannot remove `super_admin` members."
    ),
    response_model=ApiResponse[RemoveDepartmentMemberResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        RemoveDepartmentMemberResponse,
        success_message="Department member removed successfully",
        errors=(
            *ERROR_JWT,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ),
    ),
)
async def remove_department_member(
    user_id: UUID,
    auth: AuthContext = Depends(require_org_inviter),
    use_case: RemoveDepartmentMember = Depends(get_remove_department_member),
) -> ApiResponse[RemoveDepartmentMemberResponse]:
    result = await use_case.execute(
        RemoveDepartmentMemberCommand(
            department_id=auth.department_id,
            actor_user_id=auth.user_id,
            actor_role=auth.role,
            target_user_id=user_id,
        )
    )
    return success(
        RemoveDepartmentMemberResponse.model_validate(result),
        message="Department member removed successfully",
        status_code=status.HTTP_200_OK,
    )


@router.patch(
    "/users/{user_id}/role",
    summary="Change department member role",
    description=(
        "Updates a member's role in the caller's department. "
        "Requires `super_admin` or `admin`. "
        "`super_admin` may assign any department role; `admin` may only assign "
        "clinical/operational staff roles (not `super_admin` or `admin`)."
    ),
    response_model=ApiResponse[UpdateDepartmentMemberRoleResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        UpdateDepartmentMemberRoleResponse,
        success_message="Department member role updated successfully",
        errors=(
            *ERROR_JWT,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    ),
)
async def update_department_member_role(
    user_id: UUID,
    body: UpdateDepartmentMemberRoleRequest,
    auth: AuthContext = Depends(require_org_inviter),
    use_case: UpdateUserRole = Depends(get_update_user_role),
) -> ApiResponse[UpdateDepartmentMemberRoleResponse]:
    result = await use_case.execute(
        UpdateDepartmentMemberRoleCommand(
            department_id=auth.department_id,
            actor_user_id=auth.user_id,
            actor_role=auth.role,
            target_user_id=user_id,
            new_role=UserRole(body.role.value),
        )
    )
    return success(
        UpdateDepartmentMemberRoleResponse.model_validate(result),
        message="Department member role updated successfully",
        status_code=status.HTTP_200_OK,
    )
