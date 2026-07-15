"""Endpoint: check in a patient (register if new, then open an encounter)."""
from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.encounters.commands.check_in_patient import (
    CheckInPatientCommand,
)
from backend.src.application.encounters.dependencies import get_check_in_patient
from backend.src.application.encounters.use_cases.check_in_patient import CheckInPatient
from backend.src.presentation.api.v1.encounters.schemas import (
    CheckInPatientRequest,
    CheckInPatientResponse,
)
from backend.src.presentation.dependencies.auth import require_front_desk
from backend.src.presentation.openapi import ERROR_CRUD, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/check-in",
    summary="Check in a patient",
    description=(
        "Opens a new encounter for the caller's department. Pass `patient_id` for a "
        "returning patient, or full demographics to register a new one. "
        "Requires `front_desk` or `super_admin`."
    ),
    response_model=ApiResponse[CheckInPatientResponse],
    status_code=status.HTTP_201_CREATED,
    responses=envelope_responses(
        CheckInPatientResponse,
        success_status=status.HTTP_201_CREATED,
        success_message="Patient checked in successfully",
        errors=ERROR_CRUD,
    ),
)
async def check_in_patient(
    body: CheckInPatientRequest,
    auth: AuthContext = Depends(require_front_desk),
    use_case: CheckInPatient = Depends(get_check_in_patient),
) -> ApiResponse[CheckInPatientResponse]:
    result = await use_case.execute(
        CheckInPatientCommand(
            department_id=auth.department_id,
            patient_id=body.patient_id,
            first_name=body.first_name,
            last_name=body.last_name,
            date_of_birth=body.date_of_birth,
            sex=body.sex.value if body.sex else None,
            phone_number=body.phone_number,
            next_of_kin_name=body.next_of_kin_name,
            next_of_kin_phone=body.next_of_kin_phone,
            insurance_status=body.insurance_status.value,
        )
    )
    return success(
        CheckInPatientResponse.model_validate(result),
        message="Patient checked in successfully",
        status_code=status.HTTP_201_CREATED,
    )
