"""Unit tests: infrastructure/repositories/patients.py"""
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.domain.patients.entities import Patient
from backend.src.infrastructure.repositories._mappers import patient_to_entity, patient_to_model
from backend.src.infrastructure.repositories.patients import SqlAlchemyPatientRepository


def _scalar_result(*, one_or_none=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = one_or_none
    return result


def _patient(**overrides) -> Patient:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        date_of_birth=date(1990, 5, 14),
        sex="female",
        phone_number="+2348012345678",
        insurance_status="none",
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return Patient(**defaults)


@pytest.mark.asyncio
async def test_add_persists_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyPatientRepository(session)
    entity = _patient()

    result = await repo.add(entity)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once()
    assert result == patient_to_entity(patient_to_model(entity))


@pytest.mark.asyncio
async def test_get_by_id_returns_entity_when_found() -> None:
    session = AsyncMock()
    repo = SqlAlchemyPatientRepository(session)
    entity = _patient()
    model = patient_to_model(entity)
    session.execute.return_value = _scalar_result(one_or_none=model)

    assert await repo.get_by_id(entity.id) == entity


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing() -> None:
    session = AsyncMock()
    repo = SqlAlchemyPatientRepository(session)
    session.execute.return_value = _scalar_result(one_or_none=None)

    assert await repo.get_by_id(uuid4()) is None


@pytest.mark.asyncio
async def test_save_merges_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyPatientRepository(session)
    entity = _patient()
    model = patient_to_model(entity)
    session.merge.return_value = model

    result = await repo.save(entity)

    session.merge.assert_awaited_once()
    session.flush.assert_awaited_once()
    assert result == patient_to_entity(model)
