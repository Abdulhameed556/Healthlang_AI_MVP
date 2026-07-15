"""Endpoint: doctor prescribes a medication for an encounter."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.prescriptions.commands.create_prescription import (
    CreatePrescriptionCommand,
)
from backend.src.application.prescriptions.dependencies import get_create_prescription
from backend.src.application.prescriptions.use_cases.create_prescription import (
    CreatePrescription,
)
from backend.src.presentation.api.v1.prescriptions.schemas import (
    CreatePrescriptionRequest,
    CreatePrescriptionResponse,
)
from backend.src.presentation.dependencies.auth import require_doctor
from backend.src.presentation.openapi import ERROR_CRUD, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/{encounter_id}",
    summary="Prescribe a medication",
    description=(
        "Places a prescription for the encounter, advancing it to order_placed if "
        "it's still in consultation. Requires `doctor` or `super_admin`."
    ),
    response_model=ApiResponse[CreatePrescriptionResponse],
    status_code=status.HTTP_201_CREATED,
    responses=envelope_responses(
        CreatePrescriptionResponse,
        success_status=status.HTTP_201_CREATED,
        success_message="Prescription created successfully",
        errors=ERROR_CRUD,
    ),
)
async def create_prescription(
    encounter_id: UUID,
    body: CreatePrescriptionRequest,
    auth: AuthContext = Depends(require_doctor),
    use_case: CreatePrescription = Depends(get_create_prescription),
) -> ApiResponse[CreatePrescriptionResponse]:
    result = await use_case.execute(
        CreatePrescriptionCommand(
            encounter_id=encounter_id,
            ordered_by=auth.user_id,
            inventory_item_id=body.inventory_item_id,
            dosage=body.dosage,
        )
    )
    return success(
        CreatePrescriptionResponse.model_validate(result),
        message="Prescription created successfully",
        status_code=status.HTTP_201_CREATED,
    )
