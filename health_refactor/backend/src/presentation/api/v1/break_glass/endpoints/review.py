"""Endpoint: super_admin marks a break-glass access request as reviewed."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.break_glass.commands.review_break_glass_access import (
    ReviewBreakGlassAccessCommand,
)
from backend.src.application.break_glass.dependencies import (
    get_review_break_glass_access,
)
from backend.src.application.break_glass.use_cases.review_break_glass_access import (
    ReviewBreakGlassAccess,
)
from backend.src.presentation.api.v1.break_glass.schemas import (
    ReviewBreakGlassAccessResponse,
)
from backend.src.presentation.dependencies.auth import require_super_admin
from backend.src.presentation.openapi import ERROR_CRUD, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/{request_id}/review",
    summary="Mark a break-glass access request as reviewed",
    description="Requires `super_admin`.",
    response_model=ApiResponse[ReviewBreakGlassAccessResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        ReviewBreakGlassAccessResponse,
        success_message="Break-glass access request reviewed successfully",
        errors=ERROR_CRUD,
    ),
)
async def review_break_glass_access(
    request_id: UUID,
    auth: AuthContext = Depends(require_super_admin),
    use_case: ReviewBreakGlassAccess = Depends(get_review_break_glass_access),
) -> ApiResponse[ReviewBreakGlassAccessResponse]:
    result = await use_case.execute(
        ReviewBreakGlassAccessCommand(request_id=request_id, reviewed_by=auth.user_id)
    )
    return success(
        ReviewBreakGlassAccessResponse.model_validate(result),
        message="Break-glass access request reviewed successfully",
        status_code=status.HTTP_200_OK,
    )
