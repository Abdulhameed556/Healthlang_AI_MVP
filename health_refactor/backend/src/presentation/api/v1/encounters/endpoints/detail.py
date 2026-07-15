"""Endpoint: get encounter status."""
from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.src.application.auth.context import AuthContext
from backend.src.application.encounters.commands.get_encounter import GetEncounterCommand
from backend.src.application.encounters.dependencies import get_get_encounter
from backend.src.application.encounters.use_cases.get_encounter import GetEncounter
from backend.src.presentation.api.v1.encounters.schemas import EncounterResponse
from backend.src.presentation.dependencies.auth import require_auth
from backend.src.presentation.openapi import ERROR_CRUD, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/{encounter_id}",
    summary="Get encounter status",
    description="Returns an encounter's current status, ESI level, and timestamps.",
    response_model=ApiResponse[EncounterResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        EncounterResponse,
        success_message="Encounter retrieved successfully",
        errors=ERROR_CRUD,
    ),
)
async def get_encounter(
    encounter_id: UUID,
    _: AuthContext = Depends(require_auth),
    use_case: GetEncounter = Depends(get_get_encounter),
) -> ApiResponse[EncounterResponse]:
    result = await use_case.execute(GetEncounterCommand(encounter_id=encounter_id))
    return success(
        EncounterResponse.model_validate(result),
        message="Encounter retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
