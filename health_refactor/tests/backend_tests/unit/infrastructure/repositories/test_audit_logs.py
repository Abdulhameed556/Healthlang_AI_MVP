"""Unit tests: infrastructure/repositories/audit_logs.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.domain.audit.entities import AuditLog
from backend.src.domain.audit.value_objects import AuditOutcome
from backend.src.infrastructure.repositories._mappers import (
    audit_log_to_entity,
    audit_log_to_model,
)
from backend.src.infrastructure.repositories.audit_logs import SqlAlchemyAuditLogRepository


def _count_result(count: int):
    result = MagicMock()
    result.scalar_one.return_value = count
    return result


def _list_result(models):
    result = MagicMock()
    result.scalars.return_value.all.return_value = models
    return result


def _log(**overrides) -> AuditLog:
    defaults = dict(
        id=uuid4(),
        actor_id=uuid4(),
        actor_role="nurse",
        department_id=uuid4(),
        action="POST /api/v1/triage/abc",
        target_entity_id="abc",
        ip_address="127.0.0.1",
        outcome=AuditOutcome.SUCCESS.value,
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return AuditLog(**defaults)


@pytest.mark.asyncio
async def test_add_persists_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyAuditLogRepository(session)
    entity = _log()

    result = await repo.add(entity)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    assert result == audit_log_to_entity(audit_log_to_model(entity))


@pytest.mark.asyncio
async def test_list_all_returns_entities_and_total() -> None:
    session = AsyncMock()
    repo = SqlAlchemyAuditLogRepository(session)
    entity = _log()
    model = audit_log_to_model(entity)
    session.execute = AsyncMock(
        side_effect=[_count_result(1), _list_result([model])]
    )

    logs, total = await repo.list_all(page=1, page_size=20)

    assert logs == [audit_log_to_entity(model)]
    assert total == 1


@pytest.mark.asyncio
async def test_list_by_department_id_filters_and_returns_total() -> None:
    session = AsyncMock()
    repo = SqlAlchemyAuditLogRepository(session)
    dept_id = uuid4()
    entity = _log(department_id=dept_id)
    model = audit_log_to_model(entity)
    session.execute = AsyncMock(
        side_effect=[_count_result(1), _list_result([model])]
    )

    logs, total = await repo.list_by_department_id(dept_id, page=1, page_size=20)

    assert logs == [audit_log_to_entity(model)]
    assert total == 1


@pytest.mark.asyncio
async def test_list_all_returns_empty_when_none() -> None:
    session = AsyncMock()
    repo = SqlAlchemyAuditLogRepository(session)
    session.execute = AsyncMock(side_effect=[_count_result(0), _list_result([])])

    logs, total = await repo.list_all(page=1, page_size=20)

    assert logs == []
    assert total == 0
