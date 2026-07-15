"""Endpoint: add a drug to the department's inventory."""
from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.inventory.commands.create_inventory_item import (
    CreateInventoryItemCommand,
)
from backend.src.application.inventory.dependencies import get_create_inventory_item
from backend.src.application.inventory.use_cases.create_inventory_item import (
    CreateInventoryItem,
)
from backend.src.presentation.api.v1.inventory.schemas import (
    CreateInventoryItemRequest,
    InventoryItemResponse,
)
from backend.src.presentation.dependencies.auth import require_pharmacist_or_admin
from backend.src.presentation.openapi import ERROR_JWT, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/",
    summary="Add a drug to the department's inventory",
    description="Requires `pharmacist`, `admin`, or `super_admin`.",
    response_model=ApiResponse[InventoryItemResponse],
    status_code=status.HTTP_201_CREATED,
    responses=envelope_responses(
        InventoryItemResponse,
        success_status=status.HTTP_201_CREATED,
        success_message="Inventory item created successfully",
        errors=ERROR_JWT,
    ),
)
async def create_inventory_item(
    body: CreateInventoryItemRequest,
    auth: AuthContext = Depends(require_pharmacist_or_admin),
    use_case: CreateInventoryItem = Depends(get_create_inventory_item),
) -> ApiResponse[InventoryItemResponse]:
    result = await use_case.execute(
        CreateInventoryItemCommand(
            department_id=auth.department_id,
            drug_name=body.drug_name,
            quantity_on_hand=body.quantity_on_hand,
            reorder_threshold=body.reorder_threshold,
        )
    )
    return success(
        InventoryItemResponse.model_validate(result),
        message="Inventory item created successfully",
        status_code=status.HTTP_201_CREATED,
    )
