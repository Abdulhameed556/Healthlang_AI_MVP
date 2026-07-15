"""Endpoint: pharmacist dispenses a pending prescription."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.prescriptions.commands.dispense_prescription import (
    DispensePrescriptionCommand,
)
from backend.src.application.prescriptions.dependencies import get_dispense_prescription
from backend.src.application.prescriptions.use_cases.dispense_prescription import (
    DispensePrescription,
)
from backend.src.presentation.api.v1.prescriptions.schemas import (
    DispensePrescriptionResponse,
)
from backend.src.presentation.dependencies.auth import require_pharmacist
from backend.src.presentation.openapi import ERROR_CRUD, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/{prescription_id}/dispense",
    summary="Dispense a prescription",
    description=(
        "Marks the prescription dispensed and decrements the referenced inventory "
        "item by one unit. Requires `pharmacist` or `super_admin`."
    ),
    response_model=ApiResponse[DispensePrescriptionResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        DispensePrescriptionResponse,
        success_message="Prescription dispensed successfully",
        errors=(*ERROR_CRUD, status.HTTP_409_CONFLICT),
    ),
)
async def dispense_prescription(
    prescription_id: UUID,
    auth: AuthContext = Depends(require_pharmacist),
    use_case: DispensePrescription = Depends(get_dispense_prescription),
) -> ApiResponse[DispensePrescriptionResponse]:
    result = await use_case.execute(
        DispensePrescriptionCommand(
            prescription_id=prescription_id,
            dispensed_by=auth.user_id,
        )
    )
    return success(
        DispensePrescriptionResponse.model_validate(result),
        message="Prescription dispensed successfully",
        status_code=status.HTTP_200_OK,
    )
