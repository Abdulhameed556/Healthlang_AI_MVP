"""Unit tests: application/clinical_notes/use_cases/create_clinical_note.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.clinical_notes.commands.create_clinical_note import (
    CreateClinicalNoteCommand,
)
from backend.src.application.clinical_notes.use_cases.create_clinical_note import (
    CreateClinicalNote,
)
from backend.src.core.exceptions import ValidationError
from backend.src.domain.encounters.entities import Encounter
from backend.src.domain.encounters.exceptions import EncounterNotFoundError
from backend.src.domain.encounters.value_objects import EncounterStatus


def _encounter(status: EncounterStatus) -> Encounter:
    now = datetime.now(timezone.utc)
    return Encounter(
        id=uuid4(),
        patient_id=uuid4(),
        department_id=uuid4(),
        status=status.value,
        checked_in_at=now,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture()
def clinical_note_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.add = AsyncMock(side_effect=lambda note: note)
    return repo


@pytest.fixture()
def encounter_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.save = AsyncMock(side_effect=lambda encounter: encounter)
    return repo


@pytest.fixture()
def unit_of_work() -> AsyncMock:
    uow = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture()
def use_case(clinical_note_repository, encounter_repository, unit_of_work) -> CreateClinicalNote:
    return CreateClinicalNote(
        clinical_note_repository=clinical_note_repository,
        encounter_repository=encounter_repository,
        unit_of_work=unit_of_work,
    )


@pytest.mark.asyncio
async def test_execute_starts_consultation_from_triaged(
    use_case: CreateClinicalNote, encounter_repository, unit_of_work
) -> None:
    encounter = _encounter(EncounterStatus.TRIAGED)
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)

    result = await use_case.execute(
        CreateClinicalNoteCommand(
            encounter_id=encounter.id,
            doctor_id=uuid4(),
            diagnosis="Uncomplicated malaria",
            notes="Started on ACT",
        )
    )

    assert result.diagnosis == "Uncomplicated malaria"
    saved_encounter: Encounter = encounter_repository.save.await_args.args[0]
    assert saved_encounter.status == EncounterStatus.IN_CONSULTATION.value
    unit_of_work.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_adds_followup_note_without_retransitioning(
    use_case: CreateClinicalNote, encounter_repository
) -> None:
    encounter = _encounter(EncounterStatus.IN_CONSULTATION)
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)

    await use_case.execute(
        CreateClinicalNoteCommand(
            encounter_id=encounter.id,
            doctor_id=uuid4(),
            diagnosis="Follow-up",
            notes="Reviewing labs",
        )
    )

    encounter_repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_raises_when_encounter_missing(
    use_case: CreateClinicalNote, encounter_repository
) -> None:
    encounter_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(EncounterNotFoundError):
        await use_case.execute(
            CreateClinicalNoteCommand(
                encounter_id=uuid4(), doctor_id=uuid4(), diagnosis="x", notes="y"
            )
        )


@pytest.mark.asyncio
async def test_execute_rejects_note_before_triage(
    use_case: CreateClinicalNote, encounter_repository
) -> None:
    encounter = _encounter(EncounterStatus.CHECKED_IN)
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)

    with pytest.raises(ValidationError, match="Cannot write a clinical note"):
        await use_case.execute(
            CreateClinicalNoteCommand(
                encounter_id=encounter.id, doctor_id=uuid4(), diagnosis="x", notes="y"
            )
        )


@pytest.mark.asyncio
async def test_execute_rejects_note_after_discharge(
    use_case: CreateClinicalNote, encounter_repository
) -> None:
    encounter = _encounter(EncounterStatus.DISCHARGED)
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)

    with pytest.raises(ValidationError, match="Cannot write a clinical note"):
        await use_case.execute(
            CreateClinicalNoteCommand(
                encounter_id=encounter.id, doctor_id=uuid4(), diagnosis="x", notes="y"
            )
        )
