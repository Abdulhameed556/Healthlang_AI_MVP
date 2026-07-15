"""Unit tests: infrastructure/repositories/triage_records.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.domain.triage.entities import TriageRecord
from backend.src.infrastructure.repositories._mappers import (
    triage_record_to_entity,
    triage_record_to_model,
)
from backend.src.infrastructure.repositories.triage_records import (
    SqlAlchemyTriageRecordRepository,
)


def _scalar_result(*, one_or_none=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = one_or_none
    return result


def _triage_record(**overrides) -> TriageRecord:
    defaults = dict(
        id=uuid4(),
        encounter_id=uuid4(),
        recorded_by=uuid4(),
        bp_systolic=120,
        bp_diastolic=80,
        pulse=75,
        respiratory_rate=16,
        temperature=37.0,
        esi_suggested_level=3,
        esi_level=3,
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return TriageRecord(**defaults)


@pytest.mark.asyncio
async def test_add_persists_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyTriageRecordRepository(session)
    entity = _triage_record()

    result = await repo.add(entity)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once()
    assert result == triage_record_to_entity(triage_record_to_model(entity))


@pytest.mark.asyncio
async def test_get_by_encounter_id_returns_entity_when_found() -> None:
    session = AsyncMock()
    repo = SqlAlchemyTriageRecordRepository(session)
    entity = _triage_record()
    model = triage_record_to_model(entity)
    session.execute.return_value = _scalar_result(one_or_none=model)

    assert await repo.get_by_encounter_id(entity.encounter_id) == entity


@pytest.mark.asyncio
async def test_get_by_encounter_id_returns_none_when_missing() -> None:
    session = AsyncMock()
    repo = SqlAlchemyTriageRecordRepository(session)
    session.execute.return_value = _scalar_result(one_or_none=None)

    assert await repo.get_by_encounter_id(uuid4()) is None
