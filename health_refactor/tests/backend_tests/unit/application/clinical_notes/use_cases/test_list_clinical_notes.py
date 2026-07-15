"""Unit tests: application/clinical_notes/use_cases/list_clinical_notes.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.clinical_notes.commands.list_clinical_notes import (
    ListClinicalNotesCommand,
)
from backend.src.application.clinical_notes.use_cases.list_clinical_notes import (
    ListClinicalNotes,
)
from backend.src.domain.clinical_notes.entities import ClinicalNote


@pytest.mark.asyncio
async def test_execute_returns_notes_in_repository_order() -> None:
    repo = AsyncMock()
    encounter_id = uuid4()
    note = ClinicalNote(
        id=uuid4(),
        encounter_id=encounter_id,
        doctor_id=uuid4(),
        diagnosis="Malaria",
        notes="Started ACT",
        created_at=datetime.now(timezone.utc),
    )
    repo.list_by_encounter_id = AsyncMock(return_value=[note])
    use_case = ListClinicalNotes(clinical_note_repository=repo)

    result = await use_case.execute(ListClinicalNotesCommand(encounter_id=encounter_id))

    assert len(result.notes) == 1
    assert result.notes[0].diagnosis == "Malaria"


@pytest.mark.asyncio
async def test_execute_returns_empty_when_none() -> None:
    repo = AsyncMock()
    repo.list_by_encounter_id = AsyncMock(return_value=[])
    use_case = ListClinicalNotes(clinical_note_repository=repo)

    result = await use_case.execute(ListClinicalNotesCommand(encounter_id=uuid4()))

    assert result.notes == []
