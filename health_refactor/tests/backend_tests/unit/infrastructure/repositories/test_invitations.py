"""Unit tests: infrastructure/repositories/invitations.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.users.value_objects import UserRole
from backend.src.infrastructure.repositories._mappers import invitation_to_entity, invitation_to_model
from backend.src.infrastructure.repositories.invitations import SqlAlchemyInvitationRepository


def _scalar_result(*, one_or_none=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = one_or_none
    return result


@pytest.mark.asyncio
async def test_add_persists_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyInvitationRepository(session)
    now = datetime.now(timezone.utc)
    entity = Invitation(
        id=uuid4(),
        department_id=uuid4(),
        email="invite@example.com",
        role=UserRole.SUPER_ADMIN,
        token="secret",
        status=InvitationStatus.PENDING,
        expires_at=now,
        created_at=now,
    )

    result = await repo.add(entity)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once()
    assert result == invitation_to_entity(invitation_to_model(entity))


@pytest.mark.asyncio
async def test_get_pending_by_email_normalizes_email() -> None:
    session = AsyncMock()
    repo = SqlAlchemyInvitationRepository(session)
    now = datetime.now(timezone.utc)
    entity = Invitation(
        id=uuid4(),
        department_id=uuid4(),
        email="pending@example.com",
        role=UserRole.SUPER_ADMIN,
        token="tok",
        status=InvitationStatus.PENDING,
        expires_at=now,
        created_at=now,
    )
    session.execute.return_value = _scalar_result(one_or_none=invitation_to_model(entity))

    result = await repo.get_pending_by_email("Pending@Example.com")

    assert result == entity


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing() -> None:
    session = AsyncMock()
    repo = SqlAlchemyInvitationRepository(session)
    session.execute.return_value = _scalar_result(one_or_none=None)

    assert await repo.get_by_id(uuid4()) is None


@pytest.mark.asyncio
async def test_get_by_token_returns_none_when_missing() -> None:
    session = AsyncMock()
    repo = SqlAlchemyInvitationRepository(session)
    session.execute.return_value = _scalar_result(one_or_none=None)

    assert await repo.get_by_token("missing") is None


@pytest.mark.asyncio
async def test_get_pending_by_email_and_department_scopes_to_org() -> None:
    session = AsyncMock()
    repo = SqlAlchemyInvitationRepository(session)
    now = datetime.now(timezone.utc)
    dept_id = uuid4()
    entity = Invitation(
        id=uuid4(),
        department_id=dept_id,
        email="pending@example.com",
        role=UserRole.ADMIN,
        token="tok",
        status=InvitationStatus.PENDING,
        expires_at=now,
        created_at=now,
    )
    session.execute.return_value = _scalar_result(one_or_none=invitation_to_model(entity))

    result = await repo.get_pending_by_email_and_department(
        "Pending@Example.com", dept_id
    )

    assert result == entity


@pytest.mark.asyncio
async def test_save_merges_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyInvitationRepository(session)
    now = datetime.now(timezone.utc)
    entity = Invitation(
        id=uuid4(),
        department_id=uuid4(),
        email="invite@example.com",
        role=UserRole.SUPER_ADMIN,
        token="secret",
        status=InvitationStatus.ACCEPTED,
        expires_at=now,
        created_at=now,
    )
    model = invitation_to_model(entity)
    session.merge.return_value = model

    result = await repo.save(entity)

    session.merge.assert_awaited_once()
    session.flush.assert_awaited_once()
    assert result == invitation_to_entity(model)
