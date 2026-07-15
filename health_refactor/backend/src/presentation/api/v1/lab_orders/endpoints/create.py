"""Endpoint: doctor orders a lab test for an encounter."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.lab_orders.commands.create_lab_order import (
    CreateLabOrderCommand,
)
from backend.src.application.lab_orders.dependencies import get_create_lab_order
from backend.src.application.lab_orders.use_cases.create_lab_order import CreateLabOrder
from backend.src.presentation.api.v1.lab_orders.schemas import (
    CreateLabOrderRequest,
    CreateLabOrderResponse,
)
from backend.src.presentation.dependencies.auth import require_doctor
from backend.src.presentation.openapi import ERROR_CRUD, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/{encounter_id}",
    summary="Order a lab test",
    description=(
        "Places a lab order for the encounter, advancing it to order_placed if it's "
        "still in consultation. Requires `doctor` or `super_admin`."
    ),
    response_model=ApiResponse[CreateLabOrderResponse],
    status_code=status.HTTP_201_CREATED,
    responses=envelope_responses(
        CreateLabOrderResponse,
        success_status=status.HTTP_201_CREATED,
        success_message="Lab order created successfully",
        errors=ERROR_CRUD,
    ),
)
async def create_lab_order(
    encounter_id: UUID,
    body: CreateLabOrderRequest,
    auth: AuthContext = Depends(require_doctor),
    use_case: CreateLabOrder = Depends(get_create_lab_order),
) -> ApiResponse[CreateLabOrderResponse]:
    result = await use_case.execute(
        CreateLabOrderCommand(
            encounter_id=encounter_id,
            ordered_by=auth.user_id,
            test_type=body.test_type,
        )
    )
    return success(
        CreateLabOrderResponse.model_validate(result),
        message="Lab order created successfully",
        status_code=status.HTTP_201_CREATED,
    )
