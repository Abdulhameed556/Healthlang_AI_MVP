"""Endpoint: request emergency break-glass access to a patient's chart."""
from fastapi import APIRouter, Depends, Request, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.break_glass.commands.request_break_glass_access import (
    RequestBreakGlassAccessCommand,
)
from backend.src.application.break_glass.dependencies import (
    get_request_break_glass_access,
)
from backend.src.application.break_glass.use_cases.request_break_glass_access import (
    RequestBreakGlassAccess,
)
from backend.src.presentation.api.v1.break_glass.schemas import (
    RequestBreakGlassAccessRequest,
    RequestBreakGlassAccessResponse,
)
from backend.src.presentation.dependencies.auth import require_clinical_staff
from backend.src.presentation.openapi import ERROR_CRUD, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/",
    summary="Request emergency break-glass access",
    description=(
        "Grants a scoped, time-boxed read exception to a patient outside the "
        "caller's normal assignment, e.g. covering for a colleague. Always requires "
        "a reason and is auto-flagged for super_admin review. "
        "Requires `doctor`, `nurse`, or `super_admin`."
    ),
    response_model=ApiResponse[RequestBreakGlassAccessResponse],
    status_code=status.HTTP_201_CREATED,
    responses=envelope_responses(
        RequestBreakGlassAccessResponse,
        success_status=status.HTTP_201_CREATED,
        success_message="Break-glass access request recorded successfully",
        errors=ERROR_CRUD,
    ),
)
async def request_break_glass_access(
    body: RequestBreakGlassAccessRequest,
    request: Request,
    auth: AuthContext = Depends(require_clinical_staff),
    use_case: RequestBreakGlassAccess = Depends(get_request_break_glass_access),
) -> ApiResponse[RequestBreakGlassAccessResponse]:
    result = await use_case.execute(
        RequestBreakGlassAccessCommand(
            requesting_user_id=auth.user_id,
            requesting_user_role=auth.role.value,
            target_patient_id=body.target_patient_id,
            reason=body.reason,
            ip_address=request.client.host if request.client else None,
        )
    )
    return success(
        RequestBreakGlassAccessResponse.model_validate(result),
        message="Break-glass access request recorded successfully",
        status_code=status.HTTP_201_CREATED,
    )
