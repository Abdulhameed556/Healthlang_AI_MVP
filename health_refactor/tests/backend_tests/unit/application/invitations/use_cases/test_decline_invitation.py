"""Unit tests: application/invitations/use_cases/decline_invitation.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.invitations.commands.decline import DeclineInvitationCommand
from backend.src.application.invitations.use_cases.decline_invitation import DeclineInvitation
from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.mark.asyncio
async def test_decline_marks_invitation_and_user() -> None:
    now = datetime.now(timezone.utc)
    invitation = Invitation(
        id=uuid4(),
        department_id=uuid4(),
        email="invite@example.com",
        role=UserRole.SUPER_ADMIN,
        token="tok",
        status=InvitationStatus.PENDING,
        expires_at=now,
        created_at=now,
    )
    user = User(
        id=uuid4(),
        department_id=invitation.department_id,
        first_name="A",
        last_name="B",
        email=invitation.email,
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.INVITED,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        created_at=now,
        updated_at=now,
    )
    invitation_repo = AsyncMock()
    user_repo = AsyncMock()
    invitation_repo.get_by_token.return_value = invitation
    invitation_repo.save = AsyncMock(side_effect=lambda i: i)
    user_repo.get_by_email.return_value = user
    user_repo.save = AsyncMock(side_effect=lambda u: u)

    use_case = DeclineInvitation(invitation_repo, user_repo)
    result = await use_case.execute(DeclineInvitationCommand(invitation_token="tok"))

    assert result.email == "invite@example.com"
    saved_inv = invitation_repo.save.await_args.args[0]
    assert saved_inv.status == InvitationStatus.DECLINED
    saved_user = user_repo.save.await_args.args[0]
    assert saved_user.status == UserStatus.INVITATION_DECLINED


def _pending_invitation() -> Invitation:
    now = datetime.now(timezone.utc)
    return Invitation(
        id=uuid4(),
        department_id=uuid4(),
        email="invite@example.com",
        role=UserRole.ADMIN,
        token="tok",
        status=InvitationStatus.PENDING,
        expires_at=now,
        created_at=now,
    )


@pytest.mark.asyncio
async def test_decline_raises_when_invitation_not_found() -> None:
    from backend.src.domain.invitations.exceptions import InvitationNotFoundError

    invitation_repo = AsyncMock()
    invitation_repo.get_by_token.return_value = None
    use_case = DeclineInvitation(invitation_repo, AsyncMock())

    with pytest.raises(InvitationNotFoundError):
        await use_case.execute(DeclineInvitationCommand(invitation_token="missing"))


@pytest.mark.asyncio
async def test_decline_returns_early_when_already_declined() -> None:
    inv = _pending_invitation()
    inv = inv.__class__(**{**inv.__dict__, "status": InvitationStatus.DECLINED})
    invitation_repo = AsyncMock()
    invitation_repo.get_by_token.return_value = inv

    use_case = DeclineInvitation(invitation_repo, AsyncMock())
    result = await use_case.execute(DeclineInvitationCommand(invitation_token="tok"))

    assert result.email == inv.email
    invitation_repo.save.assert_not_called()


@pytest.mark.asyncio
async def test_decline_raises_when_invitation_not_pending() -> None:
    from backend.src.domain.invitations.exceptions import InvitationNotPendingError

    inv = _pending_invitation()
    inv = inv.__class__(**{**inv.__dict__, "status": InvitationStatus.ACCEPTED})
    invitation_repo = AsyncMock()
    invitation_repo.get_by_token.return_value = inv

    use_case = DeclineInvitation(invitation_repo, AsyncMock())
    with pytest.raises(InvitationNotPendingError):
        await use_case.execute(DeclineInvitationCommand(invitation_token="tok"))


@pytest.mark.asyncio
async def test_decline_skips_user_update_when_user_not_found() -> None:
    inv = _pending_invitation()
    invitation_repo = AsyncMock()
    invitation_repo.get_by_token.return_value = inv
    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = None

    use_case = DeclineInvitation(invitation_repo, user_repo)
    result = await use_case.execute(DeclineInvitationCommand(invitation_token="tok"))

    assert result.email == inv.email
    user_repo.save.assert_not_called()
