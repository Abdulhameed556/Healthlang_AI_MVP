"""Use-case: doctor writes a diagnosis/notes for an encounter.

The first note on a freshly-triaged encounter is what actually starts the
consultation — it advances the encounter from triaged to in_consultation.
Later notes on the same encounter (follow-ups while awaiting orders) don't
re-trigger a transition since the encounter is no longer in triaged.
"""
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from backend.src.application.clinical_notes.commands.create_clinical_note import (
    CreateClinicalNoteCommand,
)
from backend.src.application.clinical_notes.results.create_clinical_note import (
    CreateClinicalNoteResult,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.core.exceptions import ValidationError
from backend.src.domain.clinical_notes.entities import ClinicalNote
from backend.src.domain.clinical_notes.repositories import IClinicalNoteRepository
from backend.src.domain.encounters.exceptions import EncounterNotFoundError
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.domain.encounters.state_machine import assert_valid_transition
from backend.src.domain.encounters.value_objects import EncounterStatus

_NOTE_ALLOWED_STATUSES = frozenset({
    EncounterStatus.TRIAGED,
    EncounterStatus.IN_CONSULTATION,
    EncounterStatus.ORDER_PLACED,
    EncounterStatus.FULFILLED,
})


class CreateClinicalNote:
    def __init__(
        self,
        clinical_note_repository: IClinicalNoteRepository,
        encounter_repository: IEncounterRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._clinical_note_repository = clinical_note_repository
        self._encounter_repository = encounter_repository
        self._unit_of_work = unit_of_work

    async def execute(
        self, command: CreateClinicalNoteCommand
    ) -> CreateClinicalNoteResult:
        encounter = await self._encounter_repository.get_by_id(command.encounter_id)
        if encounter is None:
            raise EncounterNotFoundError("Encounter not found")

        status = EncounterStatus(encounter.status)
        if status not in _NOTE_ALLOWED_STATUSES:
            raise ValidationError(
                f"Cannot write a clinical note for an encounter in status '{status.value}'"
            )

        now = datetime.now(timezone.utc)
        if status == EncounterStatus.TRIAGED:
            assert_valid_transition(status, EncounterStatus.IN_CONSULTATION)
            updated_encounter = replace(
                encounter, status=EncounterStatus.IN_CONSULTATION.value, updated_at=now
            )
            await self._encounter_repository.save(updated_encounter)

        note = ClinicalNote(
            id=uuid4(),
            encounter_id=command.encounter_id,
            doctor_id=command.doctor_id,
            diagnosis=command.diagnosis,
            notes=command.notes,
            created_at=now,
        )
        note = await self._clinical_note_repository.add(note)
        await self._unit_of_work.commit()

        return CreateClinicalNoteResult(
            note_id=note.id,
            encounter_id=note.encounter_id,
            diagnosis=note.diagnosis,
            notes=note.notes,
            created_at=note.created_at,
        )
