"""Use-case: close out a visit.

Valid from in_consultation (no orders were needed) or fulfilled (orders came
back and were confirmed) — the state machine itself rejects discharging from
any other status, including order_placed with orders still outstanding.
"""
from dataclasses import replace
from datetime import datetime, timezone

from backend.src.application.encounters.commands.discharge_encounter import (
    DischargeEncounterCommand,
)
from backend.src.application.encounters.results.discharge_encounter import (
    DischargeEncounterResult,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.encounters.exceptions import EncounterNotFoundError
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.domain.encounters.state_machine import assert_valid_transition
from backend.src.domain.encounters.value_objects import EncounterStatus


class DischargeEncounter:
    def __init__(
        self,
        encounter_repository: IEncounterRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._encounter_repository = encounter_repository
        self._unit_of_work = unit_of_work

    async def execute(
        self, command: DischargeEncounterCommand
    ) -> DischargeEncounterResult:
        encounter = await self._encounter_repository.get_by_id(command.encounter_id)
        if encounter is None:
            raise EncounterNotFoundError("Encounter not found")

        current_status = EncounterStatus(encounter.status)
        assert_valid_transition(current_status, EncounterStatus.DISCHARGED)

        now = datetime.now(timezone.utc)
        updated = replace(
            encounter,
            status=EncounterStatus.DISCHARGED.value,
            closed_at=now,
            updated_at=now,
        )
        updated = await self._encounter_repository.save(updated)
        await self._unit_of_work.commit()

        return DischargeEncounterResult(
            encounter_id=updated.id,
            status=updated.status,
            closed_at=updated.closed_at,
        )
