"""Endpoint: doctor writes a clinical note for an encounter."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.clinical_notes.commands.create_clinical_note import (
    CreateClinicalNoteCommand,
)
from backend.src.application.clinical_notes.dependencies import get_create_clinical_note
from backend.src.application.clinical_notes.use_cases.create_clinical_note import (
    CreateClinicalNote,
)
from backend.src.presentation.api.v1.clinical_notes.schemas import (
    ClinicalNoteResponse,
    CreateClinicalNoteRequest,
)
from backend.src.presentation.dependencies.auth import require_doctor
from backend.src.presentation.openapi import ERROR_CRUD, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/{encounter_id}",
    summary="Write a clinical note",
    description=(
        "Records a diagnosis and notes for the encounter. The first note on a "
        "triaged encounter starts the consultation. Requires `doctor` or `super_admin`."
    ),
    response_model=ApiResponse[ClinicalNoteResponse],
    status_code=status.HTTP_201_CREATED,
    responses=envelope_responses(
        ClinicalNoteResponse,
        success_status=status.HTTP_201_CREATED,
        success_message="Clinical note recorded successfully",
        errors=ERROR_CRUD,
    ),
)
async def create_clinical_note(
    encounter_id: UUID,
    body: CreateClinicalNoteRequest,
    auth: AuthContext = Depends(require_doctor),
    use_case: CreateClinicalNote = Depends(get_create_clinical_note),
) -> ApiResponse[ClinicalNoteResponse]:
    result = await use_case.execute(
        CreateClinicalNoteCommand(
            encounter_id=encounter_id,
            doctor_id=auth.user_id,
            diagnosis=body.diagnosis,
            notes=body.notes,
        )
    )
    return success(
        ClinicalNoteResponse.model_validate(result),
        message="Clinical note recorded successfully",
        status_code=status.HTTP_201_CREATED,
    )
