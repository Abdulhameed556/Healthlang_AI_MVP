"""Unit tests: application/auth/services/invitation_acceptance.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.services.invitation_acceptance import (
    activate_invited_user_with_google,
    activate_invited_user_with_password,
    activate_department_if_invited,
    mark_invitation_accepted,
)
from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.departments.entities import Department
from backend.src.domain.departments.value_objects import DepartmentStatus
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


def _user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid4(),
        department_id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email="invite@example.com",
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.INVITED,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_mark_invitation_accepted() -> None:
    now = datetime.now(timezone.utc)
    invitation = Invitation(
        id=uuid4(),
        department_id=uuid4(),
        email="invite@example.com",
        role=UserRole.SUPER_ADMIN,
        token="token",
        status=InvitationStatus.PENDING,
        expires_at=now,
        created_at=now,
    )
    repo = AsyncMock()
    repo.save = AsyncMock(side_effect=lambda i: i)

    await mark_invitation_accepted(repo, invitation, now=now)

    saved = repo.save.await_args.args[0]
    assert saved.status == InvitationStatus.ACCEPTED
    assert saved.accepted_at == now


@pytest.mark.asyncio
async def test_activate_department_if_invited() -> None:
    now = datetime.now(timezone.utc)
    dept_id = uuid4()
    org = Department(
        id=dept_id,
        name="Emergency Department",
        status=DepartmentStatus.INVITED,
        created_at=now,
    )
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=org)
    repo.save = AsyncMock(side_effect=lambda o: o)

    await activate_department_if_invited(repo, dept_id)

    saved = repo.save.await_args.args[0]
    assert saved.status == DepartmentStatus.ACTIVE


@pytest.mark.asyncio
async def test_activate_invited_user_with_password() -> None:
    user = _user()
    now = datetime.now(timezone.utc)
    repo = AsyncMock()
    repo.save = AsyncMock(side_effect=lambda u: u)

    result = await activate_invited_user_with_password(
        repo, user, "hashed-secret", now=now
    )

    assert result.status == UserStatus.ACTIVE
    assert result.password_hash == "hashed-secret"
    assert result.auth_method == UserAuthMethod.EMAIL_PASSWORD


@pytest.mark.asyncio
async def test_activate_invited_user_with_google() -> None:
    user = _user()
    now = datetime.now(timezone.utc)
    repo = AsyncMock()
    repo.save = AsyncMock(side_effect=lambda u: u)

    result = await activate_invited_user_with_google(
        repo,
        user,
        given_name="Sam",
        family_name="User",
        now=now,
    )

    assert result.status == UserStatus.ACTIVE
    assert result.auth_method == UserAuthMethod.GOOGLE_OAUTH
    assert result.password_hash is None
    assert result.first_name == "Sam"
    assert result.last_name == "User"
