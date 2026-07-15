"""Unit tests: infrastructure/repositories/encounters.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.domain.encounters.entities import Encounter
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.infrastructure.repositories._mappers import (
    encounter_to_entity,
    encounter_to_model,
)
from backend.src.infrastructure.repositories.encounters import SqlAlchemyEncounterRepository


def _scalar_result(*, one_or_none=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = one_or_none
    return result


def _list_result(models):
    result = MagicMock()
    result.scalars.return_value.all.return_value = models
    return result


def _encounter(**overrides) -> Encounter:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid4(),
        patient_id=uuid4(),
        department_id=uuid4(),
        status=EncounterStatus.CHECKED_IN.value,
        checked_in_at=now,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return Encounter(**defaults)


@pytest.mark.asyncio
async def test_add_persists_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyEncounterRepository(session)
    entity = _encounter()

    result = await repo.add(entity)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once()
    assert result == encounter_to_entity(encounter_to_model(entity))


@pytest.mark.asyncio
async def test_get_by_id_returns_entity_when_found() -> None:
    session = AsyncMock()
    repo = SqlAlchemyEncounterRepository(session)
    entity = _encounter()
    model = encounter_to_model(entity)
    session.execute.return_value = _scalar_result(one_or_none=model)

    assert await repo.get_by_id(entity.id) == entity


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing() -> None:
    session = AsyncMock()
    repo = SqlAlchemyEncounterRepository(session)
    session.execute.return_value = _scalar_result(one_or_none=None)

    assert await repo.get_by_id(uuid4()) is None


@pytest.mark.asyncio
async def test_save_merges_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyEncounterRepository(session)
    entity = _encounter()
    model = encounter_to_model(entity)
    session.merge.return_value = model

    result = await repo.save(entity)

    session.merge.assert_awaited_once()
    session.flush.assert_awaited_once()
    assert result == encounter_to_entity(model)


@pytest.mark.asyncio
async def test_list_queue_returns_mapped_entities() -> None:
    session = AsyncMock()
    repo = SqlAlchemyEncounterRepository(session)
    dept_id = uuid4()
    entity = _encounter(department_id=dept_id, status=EncounterStatus.TRIAGED.value, esi_level=2)
    model = encounter_to_model(entity)
    session.execute.return_value = _list_result([model])

    result = await repo.list_queue(
        department_id=dept_id,
        statuses=[EncounterStatus.CHECKED_IN, EncounterStatus.TRIAGED],
    )

    assert result == [encounter_to_entity(model)]


@pytest.mark.asyncio
async def test_list_queue_returns_empty_when_none_waiting() -> None:
    session = AsyncMock()
    repo = SqlAlchemyEncounterRepository(session)
    session.execute.return_value = _list_result([])

    result = await repo.list_queue(
        department_id=uuid4(),
        statuses=[EncounterStatus.CHECKED_IN],
    )

    assert result == []
