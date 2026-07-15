"""Use-case: list an encounter's clinical notes, oldest first."""
from backend.src.application.clinical_notes.commands.list_clinical_notes import (
    ListClinicalNotesCommand,
)
from backend.src.application.clinical_notes.results.list_clinical_notes import (
    ClinicalNoteSummary,
    ListClinicalNotesResult,
)
from backend.src.domain.clinical_notes.repositories import IClinicalNoteRepository


class ListClinicalNotes:
    def __init__(self, clinical_note_repository: IClinicalNoteRepository) -> None:
        self._clinical_note_repository = clinical_note_repository

    async def execute(
        self, command: ListClinicalNotesCommand
    ) -> ListClinicalNotesResult:
        notes = await self._clinical_note_repository.list_by_encounter_id(
            command.encounter_id
        )
        return ListClinicalNotesResult(
            notes=[
                ClinicalNoteSummary(
                    note_id=note.id,
                    doctor_id=note.doctor_id,
                    diagnosis=note.diagnosis,
                    notes=note.notes,
                    created_at=note.created_at,
                )
                for note in notes
            ]
        )
