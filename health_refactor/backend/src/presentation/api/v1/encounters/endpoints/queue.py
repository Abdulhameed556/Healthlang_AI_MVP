"""Endpoint: department waiting queue."""
from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.encounters.commands.list_queue import ListQueueCommand
from backend.src.application.encounters.dependencies import get_list_queue
from backend.src.application.encounters.use_cases.list_queue import ListQueue
from backend.src.presentation.api.v1.encounters.schemas import QueueResponse
from backend.src.presentation.dependencies.auth import require_auth
from backend.src.presentation.openapi import ERROR_JWT, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/queue",
    summary="List the department's waiting queue",
    description=(
        "Encounters checked in or triaged but not yet in consultation, for the "
        "caller's department. Sorted by ESI level, then arrival time."
    ),
    response_model=ApiResponse[QueueResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        QueueResponse,
        success_message="Queue retrieved successfully",
        errors=ERROR_JWT,
    ),
)
async def list_queue(
    auth: AuthContext = Depends(require_auth),
    use_case: ListQueue = Depends(get_list_queue),
) -> ApiResponse[QueueResponse]:
    result = await use_case.execute(ListQueueCommand(department_id=auth.department_id))
    return success(
        QueueResponse.model_validate(result),
        message="Queue retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
