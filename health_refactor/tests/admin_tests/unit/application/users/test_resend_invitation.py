"""Unit tests: application/users/use_cases/resend_invitation.py + DI provider."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from admin.src.application.users.dependencies import get_resend_invitation_use_case
from admin.src.application.users.use_cases.resend_invitation import (
    ResendInvitationUseCase,
)
from admin.src.core.exceptions import ValidationError
from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus
from admin.src.domain.users.exceptions import AdminUserNotFoundError


def _user(**overrides) -> AdminUser:
    now = datetime.now(timezone.utc)
    defaults = dict(
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
        invited_by=None,
        created_at=now,
        updated_at=now,
    )
    defaults.update(overrides)
    return AdminUser(**defaults)


@pytest.fixture()
def use_case():
    session = AsyncMock()
    users = AsyncMock()
    invitations = AsyncMock()
    invitations.get_by_email = AsyncMock(return_value=None)
    invitations.save = AsyncMock(side_effect=lambda i: i)
    email = AsyncMock()

    uc = ResendInvitationUseCase(
        session=session,
        user_repository=users,
        invitation_repository=invitations,
        email_client=email,
    )
    uc._session = session
    uc._users = users
    uc._invitations = invitations
    uc._email = email
    return uc


async def test_execute_resends_for_pending_user(use_case, monkeypatch) -> None:
    monkeypatch.setattr(
        "admin.src.application.users.use_cases.resend_invitation.settings.admin_app_base_url",
        "http://localhost:3001",
    )
    user = _user()
    use_case._users.get_by_id = AsyncMock(return_value=user)

    result = await use_case.execute(user_id=user.id, invited_by=uuid4())

    assert result.email == user.email
    assert result.invitation_link.startswith("http://localhost:3001/invite?")
    use_case._session.commit.assert_awaited_once()
    use_case._email.send_invite_email.assert_awaited_once()


async def test_execute_raises_when_user_missing(use_case) -> None:
    use_case._users.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(AdminUserNotFoundError):
        await use_case.execute(user_id=uuid4(), invited_by=uuid4())


async def test_execute_raises_when_not_pending(use_case) -> None:
    user = _user(status=AdminUserStatus.ACTIVE)
    use_case._users.get_by_id = AsyncMock(return_value=user)

    with pytest.raises(ValidationError):
        await use_case.execute(user_id=user.id, invited_by=uuid4())


async def test_execute_revokes_prior_pending_invitation(use_case, monkeypatch) -> None:
    monkeypatch.setattr(
        "admin.src.application.users.use_cases.resend_invitation.settings.admin_app_base_url",
        "http://localhost:3001",
    )
    user = _user()
    use_case._users.get_by_id = AsyncMock(return_value=user)
    pending = Mock()
    pending.id = uuid4()
    use_case._invitations.get_by_email = AsyncMock(return_value=pending)

    await use_case.execute(user_id=user.id, invited_by=uuid4())

    use_case._invitations.revoke.assert_awaited_once_with(pending.id)


def test_provider_builds_use_case() -> None:
    use_case = get_resend_invitation_use_case(db=Mock())
    assert isinstance(use_case, ResendInvitationUseCase)
