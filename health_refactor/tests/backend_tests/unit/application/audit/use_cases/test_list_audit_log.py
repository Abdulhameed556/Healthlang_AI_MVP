"""Unit tests: application/audit/use_cases/list_audit_log.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.audit.commands.list_audit_log import ListAuditLogCommand
from backend.src.application.audit.use_cases.list_audit_log import ListAuditLog
from backend.src.core.exceptions import ForbiddenError
from backend.src.domain.audit.entities import AuditLog
from backend.src.domain.audit.value_objects import AuditOutcome
from backend.src.domain.users.value_objects import UserRole


def _log(**overrides) -> AuditLog:
    defaults = dict(
        id=uuid4(),
        action="POST /api/v1/triage/abc",
        outcome=AuditOutcome.SUCCESS.value,
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return AuditLog(**defaults)


@pytest.fixture()
def audit_log_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture()
def use_case(audit_log_repository) -> ListAuditLog:
    return ListAuditLog(audit_log_repository=audit_log_repository)


@pytest.mark.asyncio
async def test_super_admin_sees_all_departments(
    use_case: ListAuditLog, audit_log_repository
) -> None:
    audit_log_repository.list_all = AsyncMock(return_value=([_log()], 1))

    result = await use_case.execute(
        ListAuditLogCommand(viewer_role=UserRole.SUPER_ADMIN, viewer_department_id=uuid4())
    )

    audit_log_repository.list_all.assert_awaited_once()
    audit_log_repository.list_by_department_id.assert_not_awaited()
    assert result.total == 1
    assert result.total_pages == 1


@pytest.mark.asyncio
async def test_admin_sees_only_own_department(
    use_case: ListAuditLog, audit_log_repository
) -> None:
    dept_id = uuid4()
    audit_log_repository.list_by_department_id = AsyncMock(
        return_value=([_log(department_id=dept_id)], 1)
    )

    result = await use_case.execute(
        ListAuditLogCommand(viewer_role=UserRole.ADMIN, viewer_department_id=dept_id)
    )

    audit_log_repository.list_by_department_id.assert_awaited_once_with(
        dept_id, page=1, page_size=20
    )
    audit_log_repository.list_all.assert_not_awaited()
    assert result.logs[0].department_id == dept_id


@pytest.mark.asyncio
async def test_other_roles_are_refused(use_case: ListAuditLog, audit_log_repository) -> None:
    with pytest.raises(ForbiddenError):
        await use_case.execute(
            ListAuditLogCommand(viewer_role=UserRole.NURSE, viewer_department_id=uuid4())
        )
    audit_log_repository.list_all.assert_not_awaited()
    audit_log_repository.list_by_department_id.assert_not_awaited()
