"""Unit tests: admin/src/infrastructure/database/otp_store.py — OTPStore."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from admin.src.infrastructure.database.otp_store import OTPStore


def _make_session() -> AsyncMock:
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_save_deletes_existing_otp_and_adds_new(monkeypatch) -> None:
    session = _make_session()
    store = OTPStore(session)

    await store.save("User@Example.com", "123456")

    assert session.execute.call_count == 1  # the DELETE
    session.add.assert_called_once()
    session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_save_normalises_email_to_lowercase() -> None:
    session = _make_session()
    store = OTPStore(session)

    await store.save("UPPER@EXAMPLE.COM", "654321")

    added_obj = session.add.call_args[0][0]
    assert added_obj.email == "upper@example.com"


@pytest.mark.asyncio
async def test_save_sets_expiry_in_future() -> None:
    session = _make_session()
    store = OTPStore(session)
    before = datetime.now(timezone.utc)

    await store.save("a@b.com", "000000", ttl=600)

    added_obj = session.add.call_args[0][0]
    assert added_obj.expires_at > before + timedelta(seconds=599)


@pytest.mark.asyncio
async def test_get_returns_otp_when_found() -> None:
    session = _make_session()
    session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value="112233")
    )
    store = OTPStore(session)

    result = await store.get("a@b.com")

    assert result == "112233"


@pytest.mark.asyncio
async def test_get_returns_none_when_not_found() -> None:
    session = _make_session()
    session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=None)
    )
    store = OTPStore(session)

    result = await store.get("missing@b.com")

    assert result is None


@pytest.mark.asyncio
async def test_delete_executes_delete_and_flushes() -> None:
    session = _make_session()
    store = OTPStore(session)

    await store.delete("a@b.com")

    session.execute.assert_called_once()
    session.flush.assert_called_once()
