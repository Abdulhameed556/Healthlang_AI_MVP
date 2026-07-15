"""Endpoint: list an encounter's clinical notes."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.clinical_notes.commands.list_clinical_notes import (
    ListClinicalNotesCommand,
)
from backend.src.application.clinical_notes.dependencies import get_list_clinical_notes
from backend.src.application.clinical_notes.use_cases.list_clinical_notes import (
    ListClinicalNotes,
)
from backend.src.presentation.api.v1.clinical_notes.schemas import (
    ListClinicalNotesResponse,
)
from backend.src.presentation.dependencies.auth import require_doctor
from backend.src.presentation.openapi import ERROR_JWT, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/{encounter_id}",
    summary="List an encounter's clinical notes",
    description="Requires `doctor` or `super_admin` — diagnoses are not visible to other roles.",
    response_model=ApiResponse[ListClinicalNotesResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        ListClinicalNotesResponse,
        success_message="Clinical notes retrieved successfully",
        errors=ERROR_JWT,
    ),
)
async def list_clinical_notes(
    encounter_id: UUID,
    _: AuthContext = Depends(require_doctor),
    use_case: ListClinicalNotes = Depends(get_list_clinical_notes),
) -> ApiResponse[ListClinicalNotesResponse]:
    result = await use_case.execute(ListClinicalNotesCommand(encounter_id=encounter_id))
    return success(
        ListClinicalNotesResponse.model_validate(result),
        message="Clinical notes retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
