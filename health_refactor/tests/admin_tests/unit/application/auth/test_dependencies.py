"""Unit tests: application/auth/dependencies.py (providers + admin guards)."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

import admin.src.application.auth.dependencies as deps
from admin.src.application.auth.use_cases.accept_invitation import (
    AcceptInvitationUseCase,
)
from admin.src.application.auth.use_cases.login_with_email import LoginWithEmailUseCase
from admin.src.application.auth.use_cases.logout import LogoutUseCase
from admin.src.core.exceptions import ForbiddenError, UnauthorizedError
from admin.src.domain.auth.entities import AdminSession
from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus


def _admin_user(*, role: AdminRole = AdminRole.SUPER_ADMIN,
                status: AdminUserStatus = AdminUserStatus.ACTIVE) -> AdminUser:
    now = datetime.now(timezone.utc)
    return AdminUser(
        id=uuid4(),
        email="admin@acme.com",
        first_name="Ada",
        last_name="Min",
        role=role,
        status=status,
        password_hash="hash",
        google_linked=False,
        must_change_password=False,
        failed_attempts=0,
        invited_by=None,
        created_at=now,
        updated_at=now,
    )


def _session(user_id, *, invalidated: bool = False, expired: bool = False) -> AdminSession:
    now = datetime.now(timezone.utc)
    return AdminSession(
        id=uuid4(),
        user_id=user_id,
        token="hashed",
        created_at=now,
        expires_at=now - timedelta(hours=1) if expired else now + timedelta(hours=1),
        invalidated_at=now if invalidated else None,
    )


def _wire(monkeypatch, *, session, user, payload=None):
    """Patch repos + token helpers used inside get_current_admin."""
    session_repo = Mock()
    session_repo.get_by_token = AsyncMock(return_value=session)
    user_repo = Mock()
    user_repo.get_by_id = AsyncMock(return_value=user)
    monkeypatch.setattr(deps, "AdminSessionRepository", lambda db: session_repo)
    monkeypatch.setattr(deps, "AdminUserRepository", lambda db: user_repo)
    monkeypatch.setattr(deps, "hash_token", lambda token: "hashed")
    if payload is None:
        payload = {"sub": str(user.id) if user else str(uuid4())}
    monkeypatch.setattr(deps, "decode_token", lambda token: payload)


# ── provider functions ────────────────────────────────────────────────

def test_get_login_use_case_builds_use_case():
    assert isinstance(deps.get_login_use_case(db=Mock()), LoginWithEmailUseCase)


def test_get_logout_use_case_builds_use_case():
    assert isinstance(deps.get_logout_use_case(db=Mock()), LogoutUseCase)


# ── _bearer_token ─────────────────────────────────────────────────────

def test_bearer_token_extracts_value():
    assert deps._bearer_token("Bearer abc.def") == "abc.def"


@pytest.mark.parametrize("header", [None, "", "Token abc", "abc"])
def test_bearer_token_rejects_bad_header(header):
    with pytest.raises(UnauthorizedError):
        deps._bearer_token(header)


# ── get_current_admin ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_current_admin_returns_active_user(monkeypatch):
    user = _admin_user()
    _wire(monkeypatch, session=_session(user.id), user=user)

    result = await deps.get_current_admin(authorization="Bearer t", db=Mock())

    assert result is user


@pytest.mark.asyncio
async def test_get_current_admin_rejects_missing_header(monkeypatch):
    with pytest.raises(UnauthorizedError):
        await deps.get_current_admin(authorization=None, db=Mock())


@pytest.mark.asyncio
async def test_get_current_admin_rejects_missing_session(monkeypatch):
    user = _admin_user()
    _wire(monkeypatch, session=None, user=user)
    with pytest.raises(UnauthorizedError, match="no longer valid"):
        await deps.get_current_admin(authorization="Bearer t", db=Mock())


@pytest.mark.asyncio
async def test_get_current_admin_rejects_invalidated_session(monkeypatch):
    user = _admin_user()
    _wire(monkeypatch, session=_session(user.id, invalidated=True), user=user)
    with pytest.raises(UnauthorizedError, match="no longer valid"):
        await deps.get_current_admin(authorization="Bearer t", db=Mock())


@pytest.mark.asyncio
async def test_get_current_admin_rejects_expired_session(monkeypatch):
    user = _admin_user()
    _wire(monkeypatch, session=_session(user.id, expired=True), user=user)
    with pytest.raises(UnauthorizedError, match="expired"):
        await deps.get_current_admin(authorization="Bearer t", db=Mock())


@pytest.mark.asyncio
async def test_get_current_admin_rejects_missing_subject(monkeypatch):
    user = _admin_user()
    _wire(monkeypatch, session=_session(user.id), user=user, payload={})
    with pytest.raises(UnauthorizedError, match="Invalid token"):
        await deps.get_current_admin(authorization="Bearer t", db=Mock())


@pytest.mark.asyncio
async def test_get_current_admin_rejects_inactive_user(monkeypatch):
    user = _admin_user(status=AdminUserStatus.LOCKED)
    _wire(monkeypatch, session=_session(user.id), user=user)
    with pytest.raises(UnauthorizedError, match="not active"):
        await deps.get_current_admin(authorization="Bearer t", db=Mock())


@pytest.mark.asyncio
async def test_get_current_admin_rejects_unknown_user(monkeypatch):
    sub = uuid4()
    _wire(monkeypatch, session=_session(sub), user=None, payload={"sub": str(sub)})
    with pytest.raises(UnauthorizedError, match="not active"):
        await deps.get_current_admin(authorization="Bearer t", db=Mock())


# ── require_admin ─────────────────────────────────────────────────────

def test_require_admin_allows_admin():
    user = _admin_user(role=AdminRole.SUPER_ADMIN)
    assert deps.require_admin(current=user) is user


def test_require_admin_rejects_read_only():
    user = _admin_user(role=AdminRole.READ_ONLY)
    with pytest.raises(ForbiddenError):
        deps.require_admin(current=user)


# ── require_any_role ──────────────────────────────────────────────────

def test_require_any_role_allows_super_admin():
    user = _admin_user(role=AdminRole.SUPER_ADMIN)
    assert deps.require_any_role(current=user) is user


def test_require_any_role_allows_read_only():
    user = _admin_user(role=AdminRole.READ_ONLY)
    assert deps.require_any_role(current=user) is user


# ── get_accept_invitation_use_case ───────────────────────────────────

def test_get_accept_invitation_use_case_builds_use_case():
    use_case = deps.get_accept_invitation_use_case(db=Mock())
    assert isinstance(use_case, AcceptInvitationUseCase)
