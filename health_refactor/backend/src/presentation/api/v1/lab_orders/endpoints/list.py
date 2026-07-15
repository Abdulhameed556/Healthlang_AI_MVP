"""Endpoint: list an encounter's lab orders."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.lab_orders.commands.list_lab_orders import (
    ListLabOrdersCommand,
)
from backend.src.application.lab_orders.dependencies import get_list_lab_orders
from backend.src.application.lab_orders.use_cases.list_lab_orders import ListLabOrders
from backend.src.presentation.api.v1.lab_orders.schemas import ListLabOrdersResponse
from backend.src.presentation.dependencies.auth import require_doctor_or_lab_scientist
from backend.src.presentation.openapi import ERROR_JWT, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/{encounter_id}",
    summary="List an encounter's lab orders",
    description="Requires `doctor`, `lab_scientist`, or `super_admin`.",
    response_model=ApiResponse[ListLabOrdersResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        ListLabOrdersResponse,
        success_message="Lab orders retrieved successfully",
        errors=ERROR_JWT,
    ),
)
async def list_lab_orders(
    encounter_id: UUID,
    _: AuthContext = Depends(require_doctor_or_lab_scientist),
    use_case: ListLabOrders = Depends(get_list_lab_orders),
) -> ApiResponse[ListLabOrdersResponse]:
    result = await use_case.execute(ListLabOrdersCommand(encounter_id=encounter_id))
    return success(
        ListLabOrdersResponse.model_validate(result),
        message="Lab orders retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
