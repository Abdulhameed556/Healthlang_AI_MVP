"""Endpoint: list departments for the authenticated user."""
from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.users.commands.list_user_departments import (
    ListUserDepartmentsCommand,
)
from backend.src.application.users.dependencies import get_list_user_departments
from backend.src.application.users.use_cases.list_user_departments import (
    ListUserDepartments,
)
from backend.src.presentation.api.v1.users.schemas import ListUserDepartmentsResponse
from backend.src.presentation.dependencies.auth import require_auth
from backend.src.presentation.openapi import ERROR_JWT, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/me/departments",
    summary="List departments for current user",
    description=(
        "Returns every active department membership for the authenticated user's email. "
        "Use this to populate an org switcher; then send X-Department-Id on other routes. "
        "All roles may call this route. The optional org header does not filter this list."
    ),
    response_model=ApiResponse[ListUserDepartmentsResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        ListUserDepartmentsResponse,
        success_message="Departments retrieved successfully",
        errors=ERROR_JWT,
    ),
)
async def list_user_departments(
    auth: AuthContext = Depends(require_auth),
    use_case: ListUserDepartments = Depends(get_list_user_departments),
) -> ApiResponse[ListUserDepartmentsResponse]:
    result = await use_case.execute(ListUserDepartmentsCommand(email=auth.email))
    return success(
        ListUserDepartmentsResponse.model_validate(result),
        message="Departments retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
