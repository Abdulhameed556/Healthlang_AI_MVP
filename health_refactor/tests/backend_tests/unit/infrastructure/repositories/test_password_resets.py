"""Unit tests: infrastructure/repositories/password_resets.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.domain.auth.entities import PasswordReset
from backend.src.domain.auth.value_objects import PasswordResetStatus
from backend.src.infrastructure.repositories._password_reset_mappers import (
    password_reset_to_entity,
    password_reset_to_model,
)
from backend.src.infrastructure.repositories.password_resets import (
    SqlAlchemyPasswordResetRepository,
)


def _scalars_result(models: list) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = models
    return result


def _password_reset_entity() -> PasswordReset:
    now = datetime.now(timezone.utc)
    return PasswordReset(
        id=uuid4(),
        user_id=uuid4(),
        otp_hash="hashed-token",
        status=PasswordResetStatus.PENDING.value,
        expires_at=now,
        created_at=now,
    )


@pytest.mark.asyncio
async def test_add_persists_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyPasswordResetRepository(session)
    entity = _password_reset_entity()

    result = await repo.add(entity)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once()
    assert result == password_reset_to_entity(password_reset_to_model(entity))


@pytest.mark.asyncio
async def test_save_merges_and_returns_entity() -> None:
    session = AsyncMock()
    repo = SqlAlchemyPasswordResetRepository(session)
    entity = _password_reset_entity()
    model = password_reset_to_model(entity)
    session.merge.return_value = model

    result = await repo.save(entity)

    session.merge.assert_awaited_once()
    session.flush.assert_awaited_once()
    assert result == password_reset_to_entity(model)


@pytest.mark.asyncio
async def test_list_pending_for_user_ids_returns_empty_for_no_ids() -> None:
    session = AsyncMock()
    repo = SqlAlchemyPasswordResetRepository(session)

    assert await repo.list_pending_for_user_ids([]) == []
    session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_pending_for_user_ids_returns_entities() -> None:
    session = AsyncMock()
    repo = SqlAlchemyPasswordResetRepository(session)
    entity = _password_reset_entity()
    model = password_reset_to_model(entity)
    session.execute.return_value = _scalars_result([model])

    result = await repo.list_pending_for_user_ids([entity.user_id])

    assert result == [entity]


@pytest.mark.asyncio
async def test_expire_pending_for_user_executes_update() -> None:
    session = AsyncMock()
    repo = SqlAlchemyPasswordResetRepository(session)
    user_id = uuid4()

    await repo.expire_pending_for_user(user_id)

    session.execute.assert_awaited_once()
