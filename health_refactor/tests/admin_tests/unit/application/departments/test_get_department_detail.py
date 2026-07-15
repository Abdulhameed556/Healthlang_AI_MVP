"""Unit tests: GetDepartmentDetailUseCase."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from admin.src.application.departments.use_cases.get_department_detail import (  # noqa: E501
    GetDepartmentDetailUseCase,
)

_DEPT_ID = UUID("00000000-0000-0000-0000-000000000001")
_NOW = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)


def _org_model(status="active"):
    m = MagicMock()
    m.id = _DEPT_ID
    m.name = "Emergency Department"
    m.description = "Trauma and acute care"
    m.status = status
    m.created_at = _NOW
    return m


def _user_model(email="u@x.com", first_name="Ada", last_name="Lace",
                role="super_admin"):
    u = MagicMock()
    u.email = email
    u.first_name = first_name
    u.last_name = last_name
    u.role = role
    return u


def _session(org, users):
    session = MagicMock()

    org_result = MagicMock()
    org_result.scalar_one_or_none.return_value = org

    users_result = MagicMock()
    users_result.scalars.return_value.all.return_value = users

    session.execute = AsyncMock(side_effect=[org_result, users_result])
    return session


def _session_not_found():
    session = MagicMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=result)
    return session


# ── execute(): not found ─────────────────────────────────────────────────────


async def test_returns_none_when_org_not_found() -> None:
    uc = GetDepartmentDetailUseCase(session=_session_not_found())
    assert await uc.execute(_DEPT_ID) is None


async def test_stops_querying_after_org_not_found() -> None:
    session = _session_not_found()
    uc = GetDepartmentDetailUseCase(session=session)
    await uc.execute(_DEPT_ID)
    assert session.execute.await_count == 1


# ── execute(): org fields ────────────────────────────────────────────────────


async def test_returns_correct_org_fields() -> None:
    uc = GetDepartmentDetailUseCase(
        session=_session(_org_model(), [])
    )
    details = await uc.execute(_DEPT_ID)
    assert details is not None
    assert details.id == _DEPT_ID
    assert details.name == "Emergency Department"
    assert details.description == "Trauma and acute care"
    assert details.created_at == _NOW


# ── execute(): users ─────────────────────────────────────────────────────────


async def test_users_list_populated_correctly() -> None:
    users = [
        _user_model("a@x.com", "Ada", "Lace", "super_admin"),
        _user_model("b@x.com", "Bob", "Smith", "admin"),
    ]
    uc = GetDepartmentDetailUseCase(
        session=_session(_org_model(), users)
    )
    details = await uc.execute(_DEPT_ID)
    assert len(details.users) == 2
    assert details.users[0].email == "a@x.com"
    assert details.users[0].role == "super_admin"
    assert details.users[1].email == "b@x.com"
    assert details.users[1].role == "admin"


async def test_empty_users_list() -> None:
    uc = GetDepartmentDetailUseCase(
        session=_session(_org_model(), [])
    )
    assert (await uc.execute(_DEPT_ID)).users == []


# ── execute(): status mapping ────────────────────────────────────────────────


async def test_invited_status_maps_to_pending() -> None:
    uc = GetDepartmentDetailUseCase(
        session=_session(_org_model(status="invited"), [])
    )
    assert (await uc.execute(_DEPT_ID)).status == "pending"


async def test_active_status_maps_to_active() -> None:
    uc = GetDepartmentDetailUseCase(
        session=_session(_org_model(status="active"), [])
    )
    assert (await uc.execute(_DEPT_ID)).status == "active"
