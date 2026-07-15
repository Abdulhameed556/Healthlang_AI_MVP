"""Endpoint: current department profile."""
from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.departments.commands.get_department_profile import (
    GetDepartmentProfileCommand,
)
from backend.src.application.departments.commands.update_department_profile import (
    UpdateDepartmentProfileCommand,
)
from backend.src.application.departments.dependencies import (
    get_department_profile,
    get_update_department_profile,
)
from backend.src.application.departments.use_cases.get_department_profile import (
    GetDepartmentProfile,
)
from backend.src.application.departments.use_cases.update_department_profile import (
    UpdateDepartmentProfile,
)
from backend.src.presentation.api.v1.departments.schemas import (
    DepartmentProfileResponse,
    UpdateDepartmentProfileRequest,
)
from backend.src.presentation.dependencies.auth import require_auth, require_org_inviter
from backend.src.presentation.openapi import ERROR_JWT, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/me",
    summary="Get current department profile",
    description=(
        "Returns the department tied to the authenticated user's JWT session. "
        "All roles may call this route."
    ),
    response_model=ApiResponse[DepartmentProfileResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        DepartmentProfileResponse,
        success_message="Department profile retrieved successfully",
        errors=(*ERROR_JWT, status.HTTP_404_NOT_FOUND),
    ),
)
async def get_department_me(
    auth: AuthContext = Depends(require_auth),
    use_case: GetDepartmentProfile = Depends(get_department_profile),
) -> ApiResponse[DepartmentProfileResponse]:
    result = await use_case.execute(
        GetDepartmentProfileCommand(department_id=auth.department_id)
    )
    return success(
        DepartmentProfileResponse.model_validate(result),
        message="Department profile retrieved successfully",
        status_code=status.HTTP_200_OK,
    )


@router.patch(
    "/me",
    summary="Update current department profile",
    description=(
        "Updates `name` and/or `description` for the caller's department. "
        "Requires `super_admin` or `admin`."
    ),
    response_model=ApiResponse[DepartmentProfileResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        DepartmentProfileResponse,
        success_message="Department profile updated successfully",
        errors=(
            *ERROR_JWT,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ),
    ),
)
async def update_department_me(
    body: UpdateDepartmentProfileRequest,
    auth: AuthContext = Depends(require_org_inviter),
    use_case: UpdateDepartmentProfile = Depends(get_update_department_profile),
) -> ApiResponse[DepartmentProfileResponse]:
    result = await use_case.execute(
        UpdateDepartmentProfileCommand(
            department_id=auth.department_id,
            name=body.name,
            description=body.description,
        )
    )
    return success(
        DepartmentProfileResponse.model_validate(result),
        message="Department profile updated successfully",
        status_code=status.HTTP_200_OK,
    )
