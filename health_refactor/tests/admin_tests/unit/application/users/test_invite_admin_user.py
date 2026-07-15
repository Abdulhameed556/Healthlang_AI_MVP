"""Unit tests: application/users/use_cases/invite_admin_user.py + DI provider."""
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from admin.src.application.users.dependencies import get_invite_admin_user_use_case
from admin.src.application.users.use_cases.invite_admin_user import (
    InviteAdminUserUseCase,
)
from admin.src.core.exceptions import ConflictError
from admin.src.domain.users.entities import AdminRole


@pytest.fixture()
def use_case():
    session = AsyncMock()
    users = AsyncMock()
    users.get_by_email = AsyncMock(return_value=None)
    users.save = AsyncMock(side_effect=lambda u: u)
    invitations = AsyncMock()
    invitations.get_by_email = AsyncMock(return_value=None)
    invitations.save = AsyncMock(side_effect=lambda i: i)
    email = AsyncMock()

    uc = InviteAdminUserUseCase(
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


async def test_execute_creates_user_and_invitation_and_sends_email(use_case, monkeypatch) -> None:
    monkeypatch.setattr(
        "admin.src.application.users.use_cases.invite_admin_user.settings.admin_app_base_url",
        "http://localhost:3001",
    )
    inviter_id = uuid4()

    result = await use_case.execute(
        email="  Ada@Platform.COM  ",
        first_name="Ada",
        last_name="Min",
        role=AdminRole.READ_ONLY,
        invited_by=inviter_id,
    )

    assert result.email == "ada@platform.com"
    assert result.role == AdminRole.READ_ONLY
    assert result.invitation_link.startswith("http://localhost:3001/invite?")

    saved_user = use_case._users.save.await_args.args[0]
    assert saved_user.email == "ada@platform.com"
    assert saved_user.invited_by == inviter_id
    assert saved_user.password_hash is None

    use_case._session.commit.assert_awaited_once()
    use_case._email.send_invite_email.assert_awaited_once()


async def test_execute_raises_when_active_user_exists(use_case) -> None:
    existing = Mock()
    use_case._users.get_by_email = AsyncMock(return_value=existing)

    with pytest.raises(ConflictError):
        await use_case.execute(
            email="taken@platform.com",
            first_name="A",
            last_name="B",
            role=AdminRole.READ_ONLY,
            invited_by=uuid4(),
        )


async def test_execute_revokes_prior_pending_invitation(use_case, monkeypatch) -> None:
    monkeypatch.setattr(
        "admin.src.application.users.use_cases.invite_admin_user.settings.admin_app_base_url",
        "http://localhost:3001",
    )
    pending = Mock()
    pending.id = uuid4()
    use_case._invitations.get_by_email = AsyncMock(return_value=pending)

    await use_case.execute(
        email="ada@platform.com",
        first_name="Ada",
        last_name="Min",
        role=AdminRole.SUPER_ADMIN,
        invited_by=uuid4(),
    )

    use_case._invitations.revoke.assert_awaited_once_with(pending.id)


def test_provider_builds_use_case() -> None:
    use_case = get_invite_admin_user_use_case(db=Mock())
    assert isinstance(use_case, InviteAdminUserUseCase)
