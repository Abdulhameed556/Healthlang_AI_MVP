"""Use-case: confirm all of an encounter's orders are back and move it to fulfilled.

Deliberately manual rather than auto-triggered by the last lab/pharmacy action —
the doctor explicitly confirms the visit is ready to close, the same
human-in-the-loop stance already used for triage overrides.
"""
from dataclasses import replace
from datetime import datetime, timezone

from backend.src.application.encounters.commands.mark_orders_fulfilled import (
    MarkOrdersFulfilledCommand,
)
from backend.src.application.encounters.results.mark_orders_fulfilled import (
    MarkOrdersFulfilledResult,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.encounters.exceptions import EncounterNotFoundError
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.domain.encounters.state_machine import assert_valid_transition
from backend.src.domain.encounters.value_objects import EncounterStatus


class MarkOrdersFulfilled:
    def __init__(
        self,
        encounter_repository: IEncounterRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._encounter_repository = encounter_repository
        self._unit_of_work = unit_of_work

    async def execute(
        self, command: MarkOrdersFulfilledCommand
    ) -> MarkOrdersFulfilledResult:
        encounter = await self._encounter_repository.get_by_id(command.encounter_id)
        if encounter is None:
            raise EncounterNotFoundError("Encounter not found")

        current_status = EncounterStatus(encounter.status)
        assert_valid_transition(current_status, EncounterStatus.FULFILLED)

        updated = replace(
            encounter,
            status=EncounterStatus.FULFILLED.value,
            updated_at=datetime.now(timezone.utc),
        )
        updated = await self._encounter_repository.save(updated)
        await self._unit_of_work.commit()

        return MarkOrdersFulfilledResult(
            encounter_id=updated.id,
            status=updated.status,
        )
