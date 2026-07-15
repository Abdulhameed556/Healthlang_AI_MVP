"""Endpoint: get patient demographics."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.patients.commands.get_patient import GetPatientCommand
from backend.src.application.patients.dependencies import get_get_patient
from backend.src.application.patients.use_cases.get_patient import GetPatient
from backend.src.presentation.api.v1.patients.schemas import PatientResponse
from backend.src.presentation.dependencies.auth import require_auth
from backend.src.presentation.openapi import ERROR_CRUD, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/{patient_id}",
    summary="Get patient demographics",
    description="Returns a patient's demographics. All authenticated staff may call this route.",
    response_model=ApiResponse[PatientResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        PatientResponse,
        success_message="Patient retrieved successfully",
        errors=ERROR_CRUD,
    ),
)
async def get_patient(
    patient_id: UUID,
    _: AuthContext = Depends(require_auth),
    use_case: GetPatient = Depends(get_get_patient),
) -> ApiResponse[PatientResponse]:
    result = await use_case.execute(GetPatientCommand(patient_id=patient_id))
    return success(
        PatientResponse.model_validate(result),
        message="Patient retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
