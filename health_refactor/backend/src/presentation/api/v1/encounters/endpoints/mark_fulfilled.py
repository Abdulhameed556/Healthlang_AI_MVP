"""Endpoint: confirm an encounter's orders are all back."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.encounters.commands.mark_orders_fulfilled import (
    MarkOrdersFulfilledCommand,
)
from backend.src.application.encounters.dependencies import get_mark_orders_fulfilled
from backend.src.application.encounters.use_cases.mark_orders_fulfilled import (
    MarkOrdersFulfilled,
)
from backend.src.presentation.api.v1.encounters.schemas import (
    MarkOrdersFulfilledResponse,
)
from backend.src.presentation.dependencies.auth import require_doctor
from backend.src.presentation.openapi import ERROR_CRUD, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/{encounter_id}/mark-fulfilled",
    summary="Confirm an encounter's orders are all back",
    description=(
        "Moves the encounter from order_placed to fulfilled. "
        "Requires `doctor` or `super_admin`."
    ),
    response_model=ApiResponse[MarkOrdersFulfilledResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        MarkOrdersFulfilledResponse,
        success_message="Encounter marked fulfilled successfully",
        errors=ERROR_CRUD,
    ),
)
async def mark_orders_fulfilled(
    encounter_id: UUID,
    _: AuthContext = Depends(require_doctor),
    use_case: MarkOrdersFulfilled = Depends(get_mark_orders_fulfilled),
) -> ApiResponse[MarkOrdersFulfilledResponse]:
    result = await use_case.execute(
        MarkOrdersFulfilledCommand(encounter_id=encounter_id)
    )
    return success(
        MarkOrdersFulfilledResponse.model_validate(result),
        message="Encounter marked fulfilled successfully",
        status_code=status.HTTP_200_OK,
    )
