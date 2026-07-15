"""Unit tests: application/auth/use_cases/accept_invitation.py"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from admin.src.application.auth.use_cases.accept_invitation import (
    AcceptInvitationUseCase,
)
from admin.src.core.exceptions import ConflictError, InviteExpiredError
from admin.src.domain.auth.entities import AdminInvitation
from admin.src.domain.auth.exceptions import AdminInvitationNotFoundError
from admin.src.domain.auth.value_objects import AdminInvitationStatus
from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus
from admin.src.domain.users.exceptions import AdminUserNotFoundError


def _invitation(**overrides) -> AdminInvitation:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=uuid4(),
        email="ada@platform.com",
        role="read_only",
        token="tok-abc",
        invited_by=uuid4(),
        status=AdminInvitationStatus.PENDING,
        expires_at=now + timedelta(hours=72),
        accepted_at=None,
        created_at=now,
    )
    defaults.update(overrides)
    return AdminInvitation(**defaults)


def _user() -> AdminUser:
    now = datetime.now(timezone.utc)
    return AdminUser(
        id=uuid4(),
        email="ada@platform.com",
        first_name="Ada",
        last_name="Min",
        role=AdminRole.READ_ONLY,
        status=AdminUserStatus.PENDING,
        password_hash=None,
        google_linked=False,
        must_change_password=False,
        failed_attempts=0,
        invited_by=uuid4(),
        created_at=now,
        updated_at=now,
    )


@pytest.fixture()
def use_case():
    session = AsyncMock()
    users = AsyncMock()
    invitations = AsyncMock()
    uc = AcceptInvitationUseCase(
        session=session, user_repository=users, invitation_repository=invitations
    )
    uc._session = session
    uc._users = users
    uc._invitations = invitations
    return uc


async def test_execute_activates_user_and_marks_invitation_accepted(use_case) -> None:
    invitation = _invitation()
    user = _user()
    use_case._invitations.get_by_token = AsyncMock(return_value=invitation)
    use_case._users.get_by_email = AsyncMock(return_value=user)

    email = await use_case.execute(token="tok-abc", password="new-password123")

    assert email == user.email
    saved_user = use_case._users.save.await_args.args[0]
    assert saved_user.status == AdminUserStatus.ACTIVE
    assert saved_user.password_hash is not None

    saved_invitation = use_case._invitations.save.await_args.args[0]
    assert saved_invitation.status == AdminInvitationStatus.ACCEPTED
    assert saved_invitation.accepted_at is not None

    use_case._session.commit.assert_awaited_once()


async def test_execute_raises_when_token_not_found(use_case) -> None:
    use_case._invitations.get_by_token = AsyncMock(return_value=None)

    with pytest.raises(AdminInvitationNotFoundError):
        await use_case.execute(token="missing", password="new-password123")


async def test_execute_raises_when_already_used(use_case) -> None:
    invitation = _invitation(status=AdminInvitationStatus.ACCEPTED)
    use_case._invitations.get_by_token = AsyncMock(return_value=invitation)

    with pytest.raises(ConflictError):
        await use_case.execute(token="tok-abc", password="new-password123")


async def test_execute_raises_when_expired(use_case) -> None:
    invitation = _invitation(
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    use_case._invitations.get_by_token = AsyncMock(return_value=invitation)

    with pytest.raises(InviteExpiredError):
        await use_case.execute(token="tok-abc", password="new-password123")


async def test_execute_raises_when_user_missing(use_case) -> None:
    invitation = _invitation()
    use_case._invitations.get_by_token = AsyncMock(return_value=invitation)
    use_case._users.get_by_email = AsyncMock(return_value=None)

    with pytest.raises(AdminUserNotFoundError):
        await use_case.execute(token="tok-abc", password="new-password123")
