"""Endpoint: lab scientist uploads a result for a pending lab order."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.lab_orders.commands.fulfill_lab_order import (
    FulfillLabOrderCommand,
)
from backend.src.application.lab_orders.dependencies import get_fulfill_lab_order
from backend.src.application.lab_orders.use_cases.fulfill_lab_order import FulfillLabOrder
from backend.src.presentation.api.v1.lab_orders.schemas import (
    FulfillLabOrderRequest,
    FulfillLabOrderResponse,
)
from backend.src.presentation.dependencies.auth import require_lab_scientist
from backend.src.presentation.openapi import ERROR_CRUD, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/{lab_order_id}/fulfill",
    summary="Upload a lab result",
    description="Marks the lab order completed with its result. Requires `lab_scientist` or `super_admin`.",
    response_model=ApiResponse[FulfillLabOrderResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        FulfillLabOrderResponse,
        success_message="Lab order fulfilled successfully",
        errors=(*ERROR_CRUD, status.HTTP_409_CONFLICT),
    ),
)
async def fulfill_lab_order(
    lab_order_id: UUID,
    body: FulfillLabOrderRequest,
    auth: AuthContext = Depends(require_lab_scientist),
    use_case: FulfillLabOrder = Depends(get_fulfill_lab_order),
) -> ApiResponse[FulfillLabOrderResponse]:
    result = await use_case.execute(
        FulfillLabOrderCommand(
            lab_order_id=lab_order_id,
            fulfilled_by=auth.user_id,
            result_payload=body.result_payload,
        )
    )
    return success(
        FulfillLabOrderResponse.model_validate(result),
        message="Lab order fulfilled successfully",
        status_code=status.HTTP_200_OK,
    )
