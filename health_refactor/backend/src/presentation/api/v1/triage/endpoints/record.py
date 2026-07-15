"""Endpoint: record triage vitals and the ESI level for an encounter."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.triage.commands.record_triage import RecordTriageCommand
from backend.src.application.triage.dependencies import get_record_triage
from backend.src.application.triage.use_cases.record_triage import RecordTriage
from backend.src.presentation.api.v1.triage.schemas import (
    RecordTriageRequest,
    RecordTriageResponse,
)
from backend.src.presentation.dependencies.auth import require_nurse
from backend.src.presentation.openapi import ERROR_CRUD, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/{encounter_id}",
    summary="Record triage vitals and ESI level",
    description=(
        "Suggests an ESI level (1-5) from vitals; the nurse may accept it or "
        "override with `final_esi_level` plus a mandatory `override_reason`. "
        "Advances the encounter from checked_in to triaged. Requires `nurse` "
        "or `super_admin`."
    ),
    response_model=ApiResponse[RecordTriageResponse],
    status_code=status.HTTP_201_CREATED,
    responses=envelope_responses(
        RecordTriageResponse,
        success_status=status.HTTP_201_CREATED,
        success_message="Triage recorded successfully",
        errors=(*ERROR_CRUD, status.HTTP_409_CONFLICT),
    ),
)
async def record_triage(
    encounter_id: UUID,
    body: RecordTriageRequest,
    auth: AuthContext = Depends(require_nurse),
    use_case: RecordTriage = Depends(get_record_triage),
) -> ApiResponse[RecordTriageResponse]:
    result = await use_case.execute(
        RecordTriageCommand(
            encounter_id=encounter_id,
            recorded_by=auth.user_id,
            bp_systolic=body.bp_systolic,
            bp_diastolic=body.bp_diastolic,
            pulse=body.pulse,
            respiratory_rate=body.respiratory_rate,
            temperature=body.temperature,
            weight_kg=body.weight_kg,
            final_esi_level=body.final_esi_level,
            override_reason=body.override_reason,
        )
    )
    return success(
        RecordTriageResponse.model_validate(result),
        message="Triage recorded successfully",
        status_code=status.HTTP_201_CREATED,
    )
