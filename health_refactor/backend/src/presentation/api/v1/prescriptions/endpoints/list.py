"""Endpoint: list an encounter's prescriptions."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.prescriptions.commands.list_prescriptions import (
    ListPrescriptionsCommand,
)
from backend.src.application.prescriptions.dependencies import get_list_prescriptions
from backend.src.application.prescriptions.use_cases.list_prescriptions import (
    ListPrescriptions,
)
from backend.src.presentation.api.v1.prescriptions.schemas import (
    ListPrescriptionsResponse,
)
from backend.src.presentation.dependencies.auth import require_doctor_or_pharmacist
from backend.src.presentation.openapi import ERROR_JWT, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/{encounter_id}",
    summary="List an encounter's prescriptions",
    description="Requires `doctor`, `pharmacist`, or `super_admin`.",
    response_model=ApiResponse[ListPrescriptionsResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        ListPrescriptionsResponse,
        success_message="Prescriptions retrieved successfully",
        errors=ERROR_JWT,
    ),
)
async def list_prescriptions(
    encounter_id: UUID,
    _: AuthContext = Depends(require_doctor_or_pharmacist),
    use_case: ListPrescriptions = Depends(get_list_prescriptions),
) -> ApiResponse[ListPrescriptionsResponse]:
    result = await use_case.execute(ListPrescriptionsCommand(encounter_id=encounter_id))
    return success(
        ListPrescriptionsResponse.model_validate(result),
        message="Prescriptions retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
