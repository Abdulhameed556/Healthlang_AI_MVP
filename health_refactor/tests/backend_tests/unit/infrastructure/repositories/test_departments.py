"""Unit tests: infrastructure/repositories/departments.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.domain.departments.entities import Department
from backend.src.domain.departments.value_objects import DepartmentStatus
from backend.src.infrastructure.repositories._mappers import department_to_entity, department_to_model
from backend.src.infrastructure.repositories.departments import SqlAlchemyDepartmentRepository


def _scalar_result(*, one_or_none=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = one_or_none
    return result


@pytest.mark.asyncio
async def test_add_persists_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyDepartmentRepository(session)
    entity = Department(
        id=uuid4(),
        name="Emergency Department",
        status=DepartmentStatus.INVITED,
        created_at=datetime.now(timezone.utc),
    )

    result = await repo.add(entity)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once()
    assert result == department_to_entity(department_to_model(entity))


@pytest.mark.asyncio
async def test_get_by_id_returns_entity_when_found() -> None:
    session = AsyncMock()
    repo = SqlAlchemyDepartmentRepository(session)
    entity = Department(
        id=uuid4(),
        name="Emergency Department",
        status=DepartmentStatus.INVITED,
        created_at=datetime.now(timezone.utc),
    )
    model = department_to_model(entity)
    session.execute.return_value = _scalar_result(one_or_none=model)

    assert await repo.get_by_id(entity.id) == entity


@pytest.mark.asyncio
async def test_save_merges_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyDepartmentRepository(session)
    entity = Department(
        id=uuid4(),
        name="Emergency Department",
        status=DepartmentStatus.ACTIVE,
        created_at=datetime.now(timezone.utc),
    )
    model = department_to_model(entity)
    session.merge.return_value = model

    result = await repo.save(entity)

    session.merge.assert_awaited_once()
    session.flush.assert_awaited_once()
    assert result == department_to_entity(model)
