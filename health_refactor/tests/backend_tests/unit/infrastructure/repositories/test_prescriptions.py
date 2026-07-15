"""Unit tests: infrastructure/repositories/prescriptions.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.domain.prescriptions.entities import Prescription
from backend.src.domain.prescriptions.value_objects import PrescriptionStatus
from backend.src.infrastructure.repositories._mappers import (
    prescription_to_entity,
    prescription_to_model,
)
from backend.src.infrastructure.repositories.prescriptions import (
    SqlAlchemyPrescriptionRepository,
)


def _scalar_result(*, one_or_none=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = one_or_none
    return result


def _list_result(models):
    result = MagicMock()
    result.scalars.return_value.all.return_value = models
    return result


def _prescription(**overrides) -> Prescription:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid4(),
        encounter_id=uuid4(),
        ordered_by=uuid4(),
        inventory_item_id=uuid4(),
        dosage="500mg twice daily",
        status=PrescriptionStatus.PENDING.value,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return Prescription(**defaults)


@pytest.mark.asyncio
async def test_add_persists_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyPrescriptionRepository(session)
    entity = _prescription()

    result = await repo.add(entity)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    assert result == prescription_to_entity(prescription_to_model(entity))


@pytest.mark.asyncio
async def test_get_by_id_returns_entity_when_found() -> None:
    session = AsyncMock()
    repo = SqlAlchemyPrescriptionRepository(session)
    entity = _prescription()
    model = prescription_to_model(entity)
    session.execute.return_value = _scalar_result(one_or_none=model)

    assert await repo.get_by_id(entity.id) == entity


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing() -> None:
    session = AsyncMock()
    repo = SqlAlchemyPrescriptionRepository(session)
    session.execute.return_value = _scalar_result(one_or_none=None)

    assert await repo.get_by_id(uuid4()) is None


@pytest.mark.asyncio
async def test_save_merges_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyPrescriptionRepository(session)
    entity = _prescription()
    model = prescription_to_model(entity)
    session.merge.return_value = model

    result = await repo.save(entity)

    session.merge.assert_awaited_once()
    assert result == prescription_to_entity(model)


@pytest.mark.asyncio
async def test_list_by_encounter_id_returns_mapped_entities() -> None:
    session = AsyncMock()
    repo = SqlAlchemyPrescriptionRepository(session)
    entity = _prescription()
    model = prescription_to_model(entity)
    session.execute.return_value = _list_result([model])

    result = await repo.list_by_encounter_id(entity.encounter_id)

    assert result == [prescription_to_entity(model)]
