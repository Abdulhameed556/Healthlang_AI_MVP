"""Use-case: look up an encounter by id."""
from backend.src.application.encounters.commands.get_encounter import GetEncounterCommand
from backend.src.application.encounters.results.get_encounter import GetEncounterResult
from backend.src.domain.encounters.exceptions import EncounterNotFoundError
from backend.src.domain.encounters.repositories import IEncounterRepository


class GetEncounter:
    def __init__(self, encounter_repository: IEncounterRepository) -> None:
        self._encounter_repository = encounter_repository

    async def execute(self, command: GetEncounterCommand) -> GetEncounterResult:
        encounter = await self._encounter_repository.get_by_id(command.encounter_id)
        if encounter is None:
            raise EncounterNotFoundError("Encounter not found")

        return GetEncounterResult(
            encounter_id=encounter.id,
            patient_id=encounter.patient_id,
            department_id=encounter.department_id,
            status=encounter.status,
            esi_level=encounter.esi_level,
            checked_in_at=encounter.checked_in_at,
            closed_at=encounter.closed_at,
        )
