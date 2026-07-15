"""Unit tests: infrastructure/repositories/admin_invitations.py"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from admin.src.domain.auth.entities import AdminInvitation
from admin.src.domain.auth.value_objects import AdminInvitationStatus
from admin.src.infrastructure.database.models.admin_invitation import (
    AdminInvitation as AdminInvitationModel,
)
from admin.src.infrastructure.repositories.admin_invitations import (
    AdminInvitationRepository,
)


def _sample_invitation() -> AdminInvitation:
    now = datetime.now(timezone.utc)
    return AdminInvitation(
        id=uuid4(),
        email="invitee@platform.com",
        role="read_only",
        token="tok-abc",
        invited_by=uuid4(),
        status=AdminInvitationStatus.PENDING,
        expires_at=now + timedelta(hours=72),
        accepted_at=None,
        created_at=now,
    )


def _sample_row(inv: AdminInvitation) -> AdminInvitationModel:
    return AdminInvitationModel(
        id=inv.id,
        email=inv.email,
        role=inv.role,
        token=inv.token,
        invited_by=inv.invited_by,
        status=inv.status,
        expires_at=inv.expires_at,
        accepted_at=inv.accepted_at,
        created_at=inv.created_at,
    )


@pytest.mark.asyncio
async def test_get_by_token_returns_entity_when_found() -> None:
    inv = _sample_invitation()
    row = _sample_row(inv)
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = row
    session.execute.return_value = result

    repo = AdminInvitationRepository(session)
    found = await repo.get_by_token("tok-abc")

    assert found == inv


@pytest.mark.asyncio
async def test_get_by_token_returns_none_when_missing() -> None:
    session = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session.execute.return_value = result

    repo = AdminInvitationRepository(session)
    assert await repo.get_by_token("missing") is None


@pytest.mark.asyncio
async def test_get_by_email_returns_pending_invitation() -> None:
    inv = _sample_invitation()
    row = _sample_row(inv)
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.first.return_value = row
    session.execute.return_value = result

    repo = AdminInvitationRepository(session)
    found = await repo.get_by_email("  Invitee@Platform.COM  ")

    assert found == inv


@pytest.mark.asyncio
async def test_get_by_email_returns_none_when_no_pending() -> None:
    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.first.return_value = None
    session.execute.return_value = result

    repo = AdminInvitationRepository(session)
    assert await repo.get_by_email("nobody@platform.com") is None


@pytest.mark.asyncio
async def test_save_merges_and_returns_entity() -> None:
    inv = _sample_invitation()
    row = _sample_row(inv)
    session = AsyncMock()
    session.merge.return_value = row

    repo = AdminInvitationRepository(session)
    saved = await repo.save(inv)

    session.merge.assert_awaited_once()
    session.flush.assert_awaited_once()
    assert saved == inv


@pytest.mark.asyncio
async def test_revoke_updates_status() -> None:
    session = AsyncMock()
    repo = AdminInvitationRepository(session)

    await repo.revoke(uuid4())

    session.execute.assert_awaited_once()
