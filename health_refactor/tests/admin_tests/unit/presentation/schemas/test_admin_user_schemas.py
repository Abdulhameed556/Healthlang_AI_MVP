"""Unit tests: presentation/api/v1/users/schemas.py (admin-users management)."""
from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from admin.src.presentation.api.v1.users.schemas import (
    AcceptInvitationRequest,
    AdminUserDetailResponse,
    AdminUserListResponse,
    AdminUserSummaryResponse,
    EditAdminUserRoleRequest,
    InviteAdminUserRequest,
    InviteAdminUserResponse,
)

_NOW = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
_ID = UUID("00000000-0000-0000-0000-000000000001")


def test_invite_admin_user_request_normalizes_email() -> None:
    req = InviteAdminUserRequest(
        email="  Ada@Platform.COM  ",
        first_name="Ada",
        last_name="Min",
        role="read_only",
    )
    assert req.email == "ada@platform.com"


def test_invite_admin_user_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        InviteAdminUserRequest(
            email="not-an-email",
            first_name="Ada",
            last_name="Min",
            role="read_only",
        )


def test_invite_admin_user_request_rejects_invalid_role() -> None:
    with pytest.raises(ValidationError):
        InviteAdminUserRequest(
            email="ada@platform.com",
            first_name="Ada",
            last_name="Min",
            role="owner",
        )


def test_edit_admin_user_role_request_accepts_valid_role() -> None:
    req = EditAdminUserRoleRequest(role="super_admin")
    assert req.role == "super_admin"


def test_admin_user_summary_response_fields() -> None:
    item = AdminUserSummaryResponse(
        id=_ID,
        email="ada@platform.com",
        first_name="Ada",
        last_name="Min",
        role="super_admin",
        status="active",
        created_at=_NOW,
    )
    assert item.id == _ID
    assert item.status == "active"


def test_admin_user_list_response_total_matches_length() -> None:
    item = AdminUserSummaryResponse(
        id=_ID,
        email="ada@platform.com",
        first_name="Ada",
        last_name="Min",
        role="read_only",
        status="pending",
        created_at=_NOW,
    )
    resp = AdminUserListResponse(users=[item], total=1)
    assert resp.total == 1
    assert len(resp.users) == 1


def test_admin_user_detail_response_optional_invited_by_defaults_none() -> None:
    resp = AdminUserDetailResponse(
        id=_ID,
        email="ada@platform.com",
        first_name="Ada",
        last_name="Min",
        role="super_admin",
        status="active",
        google_linked=False,
        must_change_password=False,
        failed_attempts=0,
        created_at=_NOW,
        updated_at=_NOW,
    )
    assert resp.invited_by is None


def test_invite_admin_user_response_fields() -> None:
    resp = InviteAdminUserResponse(
        user_id=_ID,
        invitation_id=_ID,
        email="ada@platform.com",
        role="read_only",
        invitation_link="http://localhost:3001/invite?token=abc",
    )
    assert resp.invitation_link == "http://localhost:3001/invite?token=abc"


def test_accept_invitation_request_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        AcceptInvitationRequest(token="tok-abc", password="short")


def test_accept_invitation_request_accepts_valid_password() -> None:
    req = AcceptInvitationRequest(token="tok-abc", password="longenoughpw")
    assert req.token == "tok-abc"
