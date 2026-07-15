"""FastAPI dependency-injection providers for clinical_notes use-cases."""
from fastapi import Depends

from backend.src.application.clinical_notes.use_cases.create_clinical_note import (
    CreateClinicalNote,
)
from backend.src.application.clinical_notes.use_cases.list_clinical_notes import (
    ListClinicalNotes,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.clinical_notes.repositories import IClinicalNoteRepository
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.infrastructure.database.dependencies import (
    get_clinical_note_repository,
    get_encounter_repository,
    get_unit_of_work,
)


def get_create_clinical_note(
    clinical_note_repository: IClinicalNoteRepository = Depends(get_clinical_note_repository),
    encounter_repository: IEncounterRepository = Depends(get_encounter_repository),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> CreateClinicalNote:
    return CreateClinicalNote(
        clinical_note_repository=clinical_note_repository,
        encounter_repository=encounter_repository,
        unit_of_work=unit_of_work,
    )


def get_list_clinical_notes(
    clinical_note_repository: IClinicalNoteRepository = Depends(get_clinical_note_repository),
) -> ListClinicalNotes:
    return ListClinicalNotes(clinical_note_repository=clinical_note_repository)
