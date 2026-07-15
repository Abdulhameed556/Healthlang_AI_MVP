"""Use-case: record triage vitals and confirm/override the suggested ESI level.

Ties the triage vertical to the encounter state machine: a triage record can
only be added to an encounter that is still checked_in, and recording it
always advances the encounter to triaged.
"""
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from backend.src.application.triage.commands.record_triage import RecordTriageCommand
from backend.src.application.triage.results.record_triage import RecordTriageResult
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.encounters.exceptions import EncounterNotFoundError
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.domain.encounters.state_machine import assert_valid_transition
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.domain.triage.entities import TriageRecord
from backend.src.domain.triage.esi_rules import (
    assert_valid_esi_level,
    assert_valid_esi_override,
    suggest_esi_level,
)
from backend.src.domain.triage.exceptions import TriageAlreadyRecordedError
from backend.src.domain.triage.repositories import ITriageRecordRepository


class RecordTriage:
    def __init__(
        self,
        triage_repository: ITriageRecordRepository,
        encounter_repository: IEncounterRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._triage_repository = triage_repository
        self._encounter_repository = encounter_repository
        self._unit_of_work = unit_of_work

    async def execute(self, command: RecordTriageCommand) -> RecordTriageResult:
        encounter = await self._encounter_repository.get_by_id(command.encounter_id)
        if encounter is None:
            raise EncounterNotFoundError("Encounter not found")

        existing = await self._triage_repository.get_by_encounter_id(command.encounter_id)
        if existing is not None:
            raise TriageAlreadyRecordedError(
                "This encounter already has a triage record"
            )

        assert_valid_transition(EncounterStatus(encounter.status), EncounterStatus.TRIAGED)

        suggested_level = suggest_esi_level(
            bp_systolic=command.bp_systolic,
            bp_diastolic=command.bp_diastolic,
            pulse=command.pulse,
            respiratory_rate=command.respiratory_rate,
            temperature=command.temperature,
        )
        final_level = (
            command.final_esi_level
            if command.final_esi_level is not None
            else suggested_level
        )
        assert_valid_esi_level(final_level)
        assert_valid_esi_override(suggested_level, final_level, command.override_reason)

        now = datetime.now(timezone.utc)
        record = TriageRecord(
            id=uuid4(),
            encounter_id=command.encounter_id,
            recorded_by=command.recorded_by,
            bp_systolic=command.bp_systolic,
            bp_diastolic=command.bp_diastolic,
            pulse=command.pulse,
            respiratory_rate=command.respiratory_rate,
            temperature=command.temperature,
            weight_kg=command.weight_kg,
            esi_suggested_level=suggested_level,
            esi_level=final_level,
            override_reason=command.override_reason,
            created_at=now,
        )
        record = await self._triage_repository.add(record)

        updated_encounter = replace(
            encounter,
            status=EncounterStatus.TRIAGED.value,
            esi_level=final_level,
            updated_at=now,
        )
        await self._encounter_repository.save(updated_encounter)

        await self._unit_of_work.commit()

        return RecordTriageResult(
            triage_record_id=record.id,
            encounter_id=command.encounter_id,
            esi_suggested_level=suggested_level,
            esi_level=final_level,
            was_overridden=final_level != suggested_level,
        )
