"""Endpoint: list the department's drug inventory."""
from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.inventory.commands.list_inventory import ListInventoryCommand
from backend.src.application.inventory.dependencies import get_list_inventory
from backend.src.application.inventory.use_cases.list_inventory import ListInventory
from backend.src.presentation.api.v1.inventory.schemas import ListInventoryResponse
from backend.src.presentation.dependencies.auth import require_pharmacist_or_admin
from backend.src.presentation.openapi import ERROR_JWT, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/",
    summary="List the department's drug inventory",
    description="Requires `pharmacist`, `admin`, or `super_admin`.",
    response_model=ApiResponse[ListInventoryResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        ListInventoryResponse,
        success_message="Inventory retrieved successfully",
        errors=ERROR_JWT,
    ),
)
async def list_inventory(
    auth: AuthContext = Depends(require_pharmacist_or_admin),
    use_case: ListInventory = Depends(get_list_inventory),
) -> ApiResponse[ListInventoryResponse]:
    result = await use_case.execute(ListInventoryCommand(department_id=auth.department_id))
    return success(
        ListInventoryResponse.model_validate(result),
        message="Inventory retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
