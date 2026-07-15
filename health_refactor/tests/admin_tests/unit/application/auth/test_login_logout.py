"""Unit tests: login (initiate/verify + lockout) and logout use-cases."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

import admin.src.application.auth.use_cases.login_with_email as login_mod
from admin.src.application.auth.use_cases.login_with_email import (
    LoginWithEmailUseCase,
)
from admin.src.application.auth.use_cases.logout import LogoutUseCase
from admin.src.core.exceptions import AccountLockedError, UnauthorizedError
from admin.src.core.security import hash_token
from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus

_PASSWORD = "Secret123"


@pytest.fixture(autouse=True)
def _fake_password_check(monkeypatch):
    # Unit tests must not invoke real bcrypt; compare against the known pwd.
    monkeypatch.setattr(
        login_mod,
        "verify_password",
        lambda plain, hashed: plain == _PASSWORD,
    )


def _admin(
    *,
    status=AdminUserStatus.ACTIVE,
    failed=0,
    must_change=False,
) -> AdminUser:
    now = datetime.now(timezone.utc)
    return AdminUser(
        id=uuid4(),
        email="admin@example.com",
        first_name="A",
        last_name="B",
        role=AdminRole.SUPER_ADMIN,
        status=status,
        password_hash="bcrypt-hash-placeholder",
        google_linked=False,
        must_change_password=must_change,
        failed_attempts=failed,
        invited_by=None,
        created_at=now,
        updated_at=now,
    )


def _build(user):
    session = MagicMock()
    session.commit = AsyncMock()
    users = MagicMock()
    users.get_by_email = AsyncMock(return_value=user)
    users.save = AsyncMock(side_effect=lambda u: u)
    sessions = MagicMock()
    sessions.save = AsyncMock(side_effect=lambda s: s)
    otp = MagicMock()
    otp.save = AsyncMock()
    otp.get = AsyncMock()
    otp.delete = AsyncMock()
    email = MagicMock()
    email.send_otp_email = AsyncMock()
    use_case = LoginWithEmailUseCase(session, users, sessions, otp, email)
    return use_case, session, users, sessions, otp, email


class TestInitiate:
    async def test_success_sends_dev_otp(self):
        uc, _s, _u, _se, otp, email = _build(_admin())
        await uc.initiate("admin@example.com", _PASSWORD)
        otp.save.assert_awaited_once_with("admin@example.com", "123456")
        email.send_otp_email.assert_awaited_once_with(
            "admin@example.com", "123456"
        )

    async def test_success_resets_prior_failures(self):
        uc, session, users, _se, otp, _e = _build(_admin(failed=3))
        await uc.initiate("admin@example.com", _PASSWORD)
        users.save.assert_awaited()  # reset persisted
        session.commit.assert_awaited()
        otp.save.assert_awaited_once()

    async def test_unknown_user_raises_unauthorized(self):
        uc, *_ = _build(None)
        with pytest.raises(UnauthorizedError):
            await uc.initiate("nope@example.com", _PASSWORD)

    async def test_pending_user_raises_unauthorized(self):
        uc, *_ = _build(_admin(status=AdminUserStatus.PENDING))
        with pytest.raises(UnauthorizedError):
            await uc.initiate("admin@example.com", _PASSWORD)

    async def test_locked_user_raises_locked(self):
        uc, *_ = _build(_admin(status=AdminUserStatus.LOCKED))
        with pytest.raises(AccountLockedError):
            await uc.initiate("admin@example.com", _PASSWORD)

    async def test_wrong_password_increments_and_persists(self):
        user = _admin(failed=0)
        uc, session, users, _se, _o, _e = _build(user)
        with pytest.raises(UnauthorizedError):
            await uc.initiate("admin@example.com", "wrong")
        assert user.failed_attempts == 1
        users.save.assert_awaited_once()
        session.commit.assert_awaited_once()

    async def test_wrong_password_at_threshold_locks(self):
        user = _admin(failed=4)  # one more -> 5 == MAX default
        uc, _s, _u, _se, _o, _e = _build(user)
        with pytest.raises(AccountLockedError):
            await uc.initiate("admin@example.com", "wrong")
        assert user.status == AdminUserStatus.LOCKED


class TestVerify:
    async def test_success_returns_token_and_persists_session(self):
        user = _admin(must_change=True)
        uc, session, _u, sessions, otp, _e = _build(user)
        otp.get.return_value = "123456"
        token, must_change = await uc.verify("admin@example.com", "123456")
        assert token
        assert must_change is True
        otp.delete.assert_awaited_once_with("admin@example.com")
        sessions.save.assert_awaited_once()
        session.commit.assert_awaited_once()
        # token is stored hashed, never raw
        saved = sessions.save.await_args.args[0]
        assert saved.token == hash_token(token)

    async def test_missing_otp_raises(self):
        uc, _s, _u, _se, otp, _e = _build(_admin())
        otp.get.return_value = None
        with pytest.raises(UnauthorizedError):
            await uc.verify("admin@example.com", "123456")

    async def test_wrong_otp_raises(self):
        uc, _s, _u, _se, otp, _e = _build(_admin())
        otp.get.return_value = "999999"
        with pytest.raises(UnauthorizedError):
            await uc.verify("admin@example.com", "123456")

    async def test_user_vanished_after_otp_raises(self):
        uc, _s, users, _se, otp, _e = _build(_admin())
        otp.get.return_value = "123456"
        users.get_by_email.return_value = None
        with pytest.raises(UnauthorizedError):
            await uc.verify("admin@example.com", "123456")


class TestLogout:
    async def test_invalidates_hashed_token_and_commits(self):
        session = MagicMock()
        session.commit = AsyncMock()
        sessions = MagicMock()
        sessions.invalidate = AsyncMock()
        await LogoutUseCase(session, sessions).execute("raw-jwt-token")
        sessions.invalidate.assert_awaited_once_with(hash_token("raw-jwt-token"))
        session.commit.assert_awaited_once()
