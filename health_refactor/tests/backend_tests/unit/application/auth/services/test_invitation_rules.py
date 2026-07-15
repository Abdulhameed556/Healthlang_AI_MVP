"""Unit tests: application/auth/services/invitation_rules.py"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from backend.src.application.auth.services.invitation_rules import (
    ensure_invitation_pending,
    is_invitation_expired,
)
from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.exceptions import (
    InvitationExpiredError,
    InvitationNotFoundError,
    InvitationNotPendingError,
)
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.users.value_objects import UserRole


def _invitation(*, status: InvitationStatus, expires_at: datetime) -> Invitation:
    return Invitation(
        id=uuid4(),
        department_id=uuid4(),
        email="invite@example.com",
        role=UserRole.SUPER_ADMIN,
        token="token",
        status=status,
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc),
    )


def test_returns_pending_invitation() -> None:
    now = datetime.now(timezone.utc)
    invitation = _invitation(
        status=InvitationStatus.PENDING,
        expires_at=now + timedelta(hours=1),
    )
    result = ensure_invitation_pending(invitation, now=now)
    assert result is invitation


def test_raises_when_invitation_missing() -> None:
    with pytest.raises(InvitationNotFoundError):
        ensure_invitation_pending(None)


def test_raises_when_invitation_expired() -> None:
    now = datetime.now(timezone.utc)
    invitation = _invitation(
        status=InvitationStatus.PENDING,
        expires_at=now - timedelta(hours=1),
    )
    with pytest.raises(InvitationExpiredError):
        ensure_invitation_pending(invitation, now=now)


def test_raises_when_invitation_not_pending() -> None:
    now = datetime.now(timezone.utc)
    invitation = _invitation(
        status=InvitationStatus.ACCEPTED,
        expires_at=now + timedelta(hours=1),
    )
    with pytest.raises(InvitationNotPendingError):
        ensure_invitation_pending(invitation, now=now)


def test_raises_expired_error_when_status_is_expired() -> None:
    now = datetime.now(timezone.utc)
    invitation = _invitation(
        status=InvitationStatus.EXPIRED,
        expires_at=now + timedelta(hours=1),
    )
    with pytest.raises(InvitationExpiredError):
        ensure_invitation_pending(invitation, now=now)


def test_is_invitation_expired_returns_false_for_future() -> None:
    now = datetime.now(timezone.utc)
    invitation = _invitation(
        status=InvitationStatus.PENDING,
        expires_at=now + timedelta(hours=1),
    )
    assert is_invitation_expired(invitation, now=now) is False


def test_is_invitation_expired_returns_true_for_past() -> None:
    now = datetime.now(timezone.utc)
    invitation = _invitation(
        status=InvitationStatus.PENDING,
        expires_at=now - timedelta(seconds=1),
    )
    assert is_invitation_expired(invitation, now=now) is True
