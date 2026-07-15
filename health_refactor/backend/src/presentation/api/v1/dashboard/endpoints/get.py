"""Endpoint: the caller's department dashboard."""
from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.dashboard.commands.get_department_dashboard import (
    GetDepartmentDashboardCommand,
)
from backend.src.application.dashboard.dependencies import get_get_department_dashboard
from backend.src.application.dashboard.use_cases.get_department_dashboard import (
    GetDepartmentDashboard,
)
from backend.src.presentation.api.v1.dashboard.schemas import DepartmentDashboardResponse
from backend.src.presentation.dependencies.auth import require_org_inviter
from backend.src.presentation.openapi import ERROR_JWT, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/",
    summary="Get the department dashboard",
    description=(
        "Aggregate, anonymized department stats: patients seen, active vs. "
        "discharged encounters, average visit duration, ESI distribution, and "
        "low-stock inventory count. Requires `admin` or `super_admin`."
    ),
    response_model=ApiResponse[DepartmentDashboardResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        DepartmentDashboardResponse,
        success_message="Dashboard retrieved successfully",
        errors=ERROR_JWT,
    ),
)
async def get_department_dashboard(
    auth: AuthContext = Depends(require_org_inviter),
    use_case: GetDepartmentDashboard = Depends(get_get_department_dashboard),
) -> ApiResponse[DepartmentDashboardResponse]:
    result = await use_case.execute(
        GetDepartmentDashboardCommand(department_id=auth.department_id)
    )
    return success(
        DepartmentDashboardResponse.model_validate(result),
        message="Dashboard retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
