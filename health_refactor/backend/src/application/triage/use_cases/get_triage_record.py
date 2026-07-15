"""Use-case: look up an encounter's triage record."""
from backend.src.application.triage.commands.get_triage_record import (
    GetTriageRecordCommand,
)
from backend.src.application.triage.results.get_triage_record import (
    GetTriageRecordResult,
)
from backend.src.domain.triage.exceptions import TriageRecordNotFoundError
from backend.src.domain.triage.repositories import ITriageRecordRepository


class GetTriageRecord:
    def __init__(self, triage_repository: ITriageRecordRepository) -> None:
        self._triage_repository = triage_repository

    async def execute(self, command: GetTriageRecordCommand) -> GetTriageRecordResult:
        record = await self._triage_repository.get_by_encounter_id(command.encounter_id)
        if record is None:
            raise TriageRecordNotFoundError("This encounter has no triage record")

        return GetTriageRecordResult(
            triage_record_id=record.id,
            encounter_id=record.encounter_id,
            recorded_by=record.recorded_by,
            bp_systolic=record.bp_systolic,
            bp_diastolic=record.bp_diastolic,
            pulse=record.pulse,
            respiratory_rate=record.respiratory_rate,
            temperature=record.temperature,
            weight_kg=record.weight_kg,
            esi_suggested_level=record.esi_suggested_level,
            esi_level=record.esi_level,
            override_reason=record.override_reason,
            created_at=record.created_at,
        )
