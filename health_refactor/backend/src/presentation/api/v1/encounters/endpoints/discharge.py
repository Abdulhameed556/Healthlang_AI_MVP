"""Endpoint: discharge an encounter."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.encounters.commands.discharge_encounter import (
    DischargeEncounterCommand,
)
from backend.src.application.encounters.dependencies import get_discharge_encounter
from backend.src.application.encounters.use_cases.discharge_encounter import (
    DischargeEncounter,
)
from backend.src.presentation.api.v1.encounters.schemas import (
    DischargeEncounterResponse,
)
from backend.src.presentation.dependencies.auth import require_doctor
from backend.src.presentation.openapi import ERROR_CRUD, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.post(
    "/{encounter_id}/discharge",
    summary="Discharge an encounter",
    description=(
        "Closes out the visit. Valid from in_consultation (no orders were needed) "
        "or fulfilled (orders came back). Requires `doctor` or `super_admin`."
    ),
    response_model=ApiResponse[DischargeEncounterResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        DischargeEncounterResponse,
        success_message="Encounter discharged successfully",
        errors=ERROR_CRUD,
    ),
)
async def discharge_encounter(
    encounter_id: UUID,
    _: AuthContext = Depends(require_doctor),
    use_case: DischargeEncounter = Depends(get_discharge_encounter),
) -> ApiResponse[DischargeEncounterResponse]:
    result = await use_case.execute(DischargeEncounterCommand(encounter_id=encounter_id))
    return success(
        DischargeEncounterResponse.model_validate(result),
        message="Encounter discharged successfully",
        status_code=status.HTTP_200_OK,
    )
