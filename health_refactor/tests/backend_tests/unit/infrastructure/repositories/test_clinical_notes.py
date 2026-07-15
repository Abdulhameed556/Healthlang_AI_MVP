"""Unit tests: infrastructure/repositories/clinical_notes.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.domain.clinical_notes.entities import ClinicalNote
from backend.src.infrastructure.repositories._mappers import (
    clinical_note_to_entity,
    clinical_note_to_model,
)
from backend.src.infrastructure.repositories.clinical_notes import (
    SqlAlchemyClinicalNoteRepository,
)


def _list_result(models):
    result = MagicMock()
    result.scalars.return_value.all.return_value = models
    return result


def _note(**overrides) -> ClinicalNote:
    defaults = dict(
        id=uuid4(),
        encounter_id=uuid4(),
        doctor_id=uuid4(),
        diagnosis="Uncomplicated malaria",
        notes="Started on ACT",
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return ClinicalNote(**defaults)


@pytest.mark.asyncio
async def test_add_persists_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyClinicalNoteRepository(session)
    entity = _note()

    result = await repo.add(entity)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once()
    assert result == clinical_note_to_entity(clinical_note_to_model(entity))


@pytest.mark.asyncio
async def test_list_by_encounter_id_returns_mapped_entities() -> None:
    session = AsyncMock()
    repo = SqlAlchemyClinicalNoteRepository(session)
    entity = _note()
    model = clinical_note_to_model(entity)
    session.execute.return_value = _list_result([model])

    result = await repo.list_by_encounter_id(entity.encounter_id)

    assert result == [clinical_note_to_entity(model)]


@pytest.mark.asyncio
async def test_list_by_encounter_id_returns_empty_when_none() -> None:
    session = AsyncMock()
    repo = SqlAlchemyClinicalNoteRepository(session)
    session.execute.return_value = _list_result([])

    assert await repo.list_by_encounter_id(uuid4()) == []
