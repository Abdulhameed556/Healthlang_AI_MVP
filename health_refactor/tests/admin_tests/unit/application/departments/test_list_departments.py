"""Unit tests: ListDepartmentsUseCase."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from admin.src.application.departments.use_cases.list_departments import (
    ListDepartmentsUseCase,
)

_NOW = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
_DEPT_ID = UUID("00000000-0000-0000-0000-000000000001")


def _org(
    id=_DEPT_ID,
    name="Emergency Department",
    status="active",
    created_at=_NOW,
):
    m = MagicMock()
    m.id = id
    m.name = name
    m.status = status
    m.created_at = created_at
    return m


def _session(models):
    session = MagicMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = models
    session.execute = AsyncMock(return_value=result)
    return session


# ── execute(): return shape ──────────────────────────────────────────────────


async def test_empty_db_returns_empty_list() -> None:
    uc = ListDepartmentsUseCase(session=_session([]))
    result = await uc.execute()
    assert result == []


async def test_returns_org_summary_with_correct_fields() -> None:
    uc = ListDepartmentsUseCase(session=_session([_org()]))
    orgs = await uc.execute()
    assert len(orgs) == 1
    o = orgs[0]
    assert o.id == _DEPT_ID
    assert o.name == "Emergency Department"
    assert o.created_at == _NOW


async def test_multiple_orgs_all_returned() -> None:
    id2 = UUID("00000000-0000-0000-0000-000000000002")
    uc = ListDepartmentsUseCase(
        session=_session([_org(), _org(id=id2, name="Beta Inc")])
    )
    orgs = await uc.execute()
    assert len(orgs) == 2
    assert orgs[1].name == "Beta Inc"


# ── execute(): status mapping ────────────────────────────────────────────────


async def test_invited_maps_to_pending() -> None:
    uc = ListDepartmentsUseCase(session=_session([_org(status="invited")]))
    assert (await uc.execute())[0].status == "pending"


async def test_active_maps_to_active() -> None:
    uc = ListDepartmentsUseCase(session=_session([_org(status="active")]))
    assert (await uc.execute())[0].status == "active"


async def test_disabled_maps_to_disabled() -> None:
    uc = ListDepartmentsUseCase(session=_session([_org(status="disabled")]))
    assert (await uc.execute())[0].status == "disabled"


async def test_unknown_status_returned_as_is() -> None:
    uc = ListDepartmentsUseCase(
        session=_session([_org(status="unknown_future")])
    )
    assert (await uc.execute())[0].status == "unknown_future"
