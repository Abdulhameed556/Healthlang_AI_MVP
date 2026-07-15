"""Unit tests: AdminSessionRepository (session mocked)."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from admin.src.domain.auth.entities import AdminSession
from admin.src.infrastructure.repositories.admin_sessions import (
    AdminSessionRepository,
    _to_entity,
    _to_model,
)


def _entity() -> AdminSession:
    now = datetime.now(timezone.utc)
    return AdminSession(
        id=uuid4(),
        user_id=uuid4(),
        token="hash-value",
        created_at=now,
        expires_at=now + timedelta(minutes=60),
        invalidated_at=None,
    )


class TestMappers:
    def test_entity_model_roundtrip(self):
        entity = _entity()
        model = _to_model(entity)
        assert model.token == "hash-value"
        back = _to_entity(model)
        assert back.token == entity.token
        assert back.user_id == entity.user_id


class TestRepository:
    async def test_get_by_token_found(self):
        session = MagicMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = _to_model(_entity())
        session.execute = AsyncMock(return_value=result)
        out = await AdminSessionRepository(session).get_by_token("hash-value")
        assert out is not None
        assert out.token == "hash-value"

    async def test_get_by_token_missing(self):
        session = MagicMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result)
        out = await AdminSessionRepository(session).get_by_token("nope")
        assert out is None

    async def test_save_flushes_and_returns_entity(self):
        session = MagicMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        entity = _entity()
        out = await AdminSessionRepository(session).save(entity)
        session.add.assert_called_once()
        session.flush.assert_awaited_once()
        assert out.token == entity.token

    async def test_invalidate_executes_update(self):
        session = MagicMock()
        session.execute = AsyncMock()
        await AdminSessionRepository(session).invalidate("hash-value")
        session.execute.assert_awaited_once()
