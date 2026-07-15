"""Use-case: list the department's waiting queue.

Sort order: ESI level ascending, then arrival time ascending — a level-2 patient
always jumps a level-4 patient regardless of arrival order; within the same
level, first-come-first-served. Untriaged patients (no ESI level yet) sort
after any already-triaged patient at the same conceptual priority.
"""
from backend.src.application.encounters.commands.list_queue import ListQueueCommand
from backend.src.application.encounters.results.list_queue import (
    ListQueueResult,
    QueueEntry,
)
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.domain.encounters.value_objects import EncounterStatus

_QUEUE_STATUSES = [EncounterStatus.CHECKED_IN, EncounterStatus.TRIAGED]


class ListQueue:
    def __init__(self, encounter_repository: IEncounterRepository) -> None:
        self._encounter_repository = encounter_repository

    async def execute(self, command: ListQueueCommand) -> ListQueueResult:
        encounters = await self._encounter_repository.list_queue(
            department_id=command.department_id,
            statuses=_QUEUE_STATUSES,
        )
        return ListQueueResult(
            entries=[
                QueueEntry(
                    encounter_id=encounter.id,
                    patient_id=encounter.patient_id,
                    status=encounter.status,
                    esi_level=encounter.esi_level,
                    checked_in_at=encounter.checked_in_at,
                )
                for encounter in encounters
            ]
        )
