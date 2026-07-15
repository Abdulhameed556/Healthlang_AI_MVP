"""Endpoint: list break-glass access requests awaiting review."""
from fastapi import APIRouter, Depends, status

from backend.src.application.break_glass.commands.list_break_glass_access import (
    ListBreakGlassAccessCommand,
)
from backend.src.application.break_glass.dependencies import get_list_break_glass_access
from backend.src.application.break_glass.use_cases.list_break_glass_access import (
    ListBreakGlassAccess,
)
from backend.src.presentation.api.v1.break_glass.schemas import (
    ListBreakGlassAccessResponse,
)
from backend.src.presentation.dependencies.auth import require_super_admin
from backend.src.presentation.openapi import ERROR_JWT, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/",
    summary="List break-glass access requests awaiting review",
    description="Requires `super_admin`.",
    response_model=ApiResponse[ListBreakGlassAccessResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        ListBreakGlassAccessResponse,
        success_message="Break-glass access requests retrieved successfully",
        errors=ERROR_JWT,
    ),
)
async def list_break_glass_access(
    _=Depends(require_super_admin),
    use_case: ListBreakGlassAccess = Depends(get_list_break_glass_access),
) -> ApiResponse[ListBreakGlassAccessResponse]:
    result = await use_case.execute(ListBreakGlassAccessCommand())
    return success(
        ListBreakGlassAccessResponse.model_validate(result),
        message="Break-glass access requests retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
