"""Endpoint: get an encounter's triage record."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.triage.commands.get_triage_record import (
    GetTriageRecordCommand,
)
from backend.src.application.triage.dependencies import get_get_triage_record
from backend.src.application.triage.use_cases.get_triage_record import GetTriageRecord
from backend.src.presentation.api.v1.triage.schemas import TriageRecordResponse
from backend.src.presentation.dependencies.auth import require_auth
from backend.src.presentation.openapi import ERROR_CRUD, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/{encounter_id}",
    summary="Get an encounter's triage record",
    description="Returns the vitals, suggested and final ESI level, and any override reason.",
    response_model=ApiResponse[TriageRecordResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        TriageRecordResponse,
        success_message="Triage record retrieved successfully",
        errors=ERROR_CRUD,
    ),
)
async def get_triage_record(
    encounter_id: UUID,
    _: AuthContext = Depends(require_auth),
    use_case: GetTriageRecord = Depends(get_get_triage_record),
) -> ApiResponse[TriageRecordResponse]:
    result = await use_case.execute(GetTriageRecordCommand(encounter_id=encounter_id))
    return success(
        TriageRecordResponse.model_validate(result),
        message="Triage record retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
