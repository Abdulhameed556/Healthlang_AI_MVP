"""Unit tests: admin/src/presentation/api/v1/departments/schemas.py"""
from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from admin.src.presentation.api.v1.departments.schemas import (
    InviteProductUserRequest,
    DepartmentDetailResponse,
    DepartmentListItem,
    DepartmentListResponse,
    DepartmentUserItem,
    _normalise_email,
)


def test_normalise_email_strips_and_lowercases() -> None:
    assert _normalise_email("  User@Example.COM  ") == "user@example.com"


def test_normalise_email_raises_for_missing_at() -> None:
    with pytest.raises(ValueError, match="Invalid email"):
        _normalise_email("notanemail")


def test_normalise_email_raises_for_leading_at() -> None:
    with pytest.raises(ValueError, match="Invalid email"):
        _normalise_email("@domain.com")


def test_normalise_email_raises_for_trailing_at() -> None:
    with pytest.raises(ValueError, match="Invalid email"):
        _normalise_email("user@")


def test_invite_product_user_request_normalises_email() -> None:
    req = InviteProductUserRequest(
        email="  Admin@EXAMPLE.COM  ",
        department_name="Emergency Department",
        first_name="John",
        last_name="Doe",
    )
    assert req.email == "admin@example.com"


def test_invite_product_user_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        InviteProductUserRequest(
            email="bad",
            department_name="Emergency Department",
            first_name="John",
            last_name="Doe",
        )


# ── DepartmentListItem ─────────────────────────────────────────────────────

_NOW = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
_ORG_UUID = UUID("00000000-0000-0000-0000-000000000001")


def test_org_list_item_accepts_valid_fields() -> None:
    item = DepartmentListItem(
        id=_ORG_UUID,
        name="Emergency Department",
        status="active",
        created_at=_NOW,
    )
    assert item.id == _ORG_UUID
    assert item.name == "Emergency Department"
    assert item.status == "active"


def test_org_list_response_total_matches_length() -> None:
    item = DepartmentListItem(
        id=_ORG_UUID,
        name="Radiology",
        status="pending",
        created_at=_NOW,
    )
    resp = DepartmentListResponse(departments=[item], total=1)
    assert resp.total == 1
    assert len(resp.departments) == 1


def test_org_list_response_empty() -> None:
    resp = DepartmentListResponse(departments=[], total=0)
    assert resp.departments == []
    assert resp.total == 0


# ── DepartmentUserItem ──────────────────────────────────────────────────────────────


def test_org_user_item_fields() -> None:
    user = DepartmentUserItem(
        email="ada@hospital.example",
        first_name="Ada",
        last_name="Lovelace",
        role="super_admin",
    )
    assert user.email == "ada@hospital.example"
    assert user.role == "super_admin"


# ── DepartmentDetailResponse ───────────────────────────────────────────────


def test_org_detail_response_with_all_fields() -> None:
    user = DepartmentUserItem(
        email="ada@hospital.example",
        first_name="Ada",
        last_name="Lovelace",
        role="super_admin",
    )
    resp = DepartmentDetailResponse(
        id=_ORG_UUID,
        name="Emergency Department",
        description="Trauma and acute care",
        status="active",
        created_at=_NOW,
        users=[user],
    )
    assert len(resp.users) == 1
    assert resp.users[0].email == "ada@hospital.example"


def test_org_detail_response_optional_fields_default_none() -> None:
    resp = DepartmentDetailResponse(
        id=_ORG_UUID,
        name="Radiology",
        status="pending",
        created_at=_NOW,
        users=[],
    )
    assert resp.description is None
