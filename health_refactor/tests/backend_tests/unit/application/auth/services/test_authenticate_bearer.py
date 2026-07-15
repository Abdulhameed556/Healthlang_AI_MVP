"""Unit tests: application/auth/services/authenticate_bearer.py"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from jose import JWTError

import backend.src.application.auth.services.authenticate_bearer as auth_bearer
from backend.src.application.auth.services.authenticate_bearer import authenticate_bearer_token
from backend.src.application.auth.services.session_tokens import build_user_session
from backend.src.core.exceptions import ForbiddenError, UnauthorizedError
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.fixture()
def jwt_settings(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.src.application.auth.services.session_tokens.settings.jwt_secret_key",
        "test-secret-key-for-auth-bearer",
    )
    monkeypatch.setattr(
        "backend.src.application.auth.services.session_tokens.settings.jwt_algorithm",
        "HS256",
    )
    monkeypatch.setattr(
        "backend.src.application.auth.services.session_tokens.settings.jwt_access_token_expire_minutes",
        60,
    )


def _active_user(
    *,
    user_id=None,
    department_id=None,
    email: str = "ada@example.com",
    role: UserRole = UserRole.ADMIN,
) -> User:
    now = datetime.now(timezone.utc)
    uid = user_id or uuid4()
    return User(
        id=uid,
        department_id=department_id or uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email=email,
        role=role,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        password_hash="hashed",
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_authenticate_bearer_token_returns_auth_context(jwt_settings) -> None:
    user = _active_user(role=UserRole.SUPER_ADMIN)
    token, _, session = build_user_session(user.id)
    user_repo = AsyncMock()
    session_repo = AsyncMock()
    user_repo.get_by_id = AsyncMock(return_value=user)
    session_repo.get_by_token = AsyncMock(return_value=session)

    context = await authenticate_bearer_token(
        token,
        user_repository=user_repo,
        session_repository=session_repo,
    )

    assert context.user_id == user.id
    assert context.department_id == user.department_id
    assert context.email == user.email
    assert context.role == UserRole.SUPER_ADMIN


@pytest.mark.asyncio
async def test_authenticate_bearer_token_rejects_missing_token() -> None:
    user_repo = AsyncMock()
    session_repo = AsyncMock()

    with pytest.raises(UnauthorizedError, match="Missing or invalid access token"):
        await authenticate_bearer_token(
            "",
            user_repository=user_repo,
            session_repository=session_repo,
        )


@pytest.mark.asyncio
async def test_authenticate_bearer_token_rejects_unknown_session(jwt_settings) -> None:
    user = _active_user()
    token, _, _ = build_user_session(user.id)
    user_repo = AsyncMock()
    session_repo = AsyncMock()
    session_repo.get_by_token = AsyncMock(return_value=None)

    with pytest.raises(UnauthorizedError, match="Missing or invalid access token"):
        await authenticate_bearer_token(
            token,
            user_repository=user_repo,
            session_repository=session_repo,
        )


@pytest.mark.asyncio
async def test_authenticate_bearer_token_rejects_expired_session(jwt_settings) -> None:
    user = _active_user()
    token, _, session = build_user_session(user.id)
    expired_session = type(session)(
        id=session.id,
        user_id=session.user_id,
        token=session.token,
        created_at=session.created_at,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        invalidated_at=None,
    )
    user_repo = AsyncMock()
    session_repo = AsyncMock()
    session_repo.get_by_token = AsyncMock(return_value=expired_session)

    with pytest.raises(UnauthorizedError, match="Access token has expired"):
        await authenticate_bearer_token(
            token,
            user_repository=user_repo,
            session_repository=session_repo,
        )


@pytest.mark.asyncio
async def test_authenticate_bearer_token_rejects_non_active_user(jwt_settings) -> None:
    user = _active_user()
    user = type(user)(
        **{**user.__dict__, "status": UserStatus.SUSPENDED}
    )
    token, _, session = build_user_session(user.id)
    user_repo = AsyncMock()
    session_repo = AsyncMock()
    user_repo.get_by_id = AsyncMock(return_value=user)
    session_repo.get_by_token = AsyncMock(return_value=session)

    with pytest.raises(ForbiddenError, match="Account is not active"):
        await authenticate_bearer_token(
            token,
            user_repository=user_repo,
            session_repository=session_repo,
        )


@pytest.mark.asyncio
async def test_authenticate_bearer_token_rejects_invalid_jwt(monkeypatch) -> None:
    monkeypatch.setattr(
        auth_bearer, "decode_token",
        lambda _t: (_ for _ in ()).throw(JWTError("bad")),
    )
    with pytest.raises(UnauthorizedError, match="Missing or invalid access token"):
        await authenticate_bearer_token(
            "garbage", user_repository=AsyncMock(), session_repository=AsyncMock()
        )


@pytest.mark.asyncio
async def test_authenticate_bearer_token_rejects_missing_subject(monkeypatch) -> None:
    monkeypatch.setattr(auth_bearer, "decode_token", lambda _t: {})
    with pytest.raises(UnauthorizedError, match="Missing or invalid access token"):
        await authenticate_bearer_token(
            "tok", user_repository=AsyncMock(), session_repository=AsyncMock()
        )


@pytest.mark.asyncio
async def test_authenticate_bearer_token_rejects_non_uuid_subject(monkeypatch) -> None:
    monkeypatch.setattr(auth_bearer, "decode_token", lambda _t: {"sub": "not-a-uuid"})
    with pytest.raises(UnauthorizedError, match="Missing or invalid access token"):
        await authenticate_bearer_token(
            "tok", user_repository=AsyncMock(), session_repository=AsyncMock()
        )


@pytest.mark.asyncio
async def test_authenticate_bearer_token_rejects_session_user_mismatch(jwt_settings) -> None:
    user = _active_user()
    token, _, session = build_user_session(user.id)
    mismatched = type(session)(
        id=session.id,
        user_id=uuid4(),  # belongs to a different user
        token=session.token,
        created_at=session.created_at,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        invalidated_at=None,
    )
    session_repo = AsyncMock()
    session_repo.get_by_token = AsyncMock(return_value=mismatched)

    with pytest.raises(UnauthorizedError, match="Missing or invalid access token"):
        await authenticate_bearer_token(
            token, user_repository=AsyncMock(), session_repository=session_repo
        )


@pytest.mark.asyncio
async def test_authenticate_bearer_token_uses_login_org_when_header_omitted(
    jwt_settings,
) -> None:
    user = _active_user(role=UserRole.SUPER_ADMIN)
    token, _, session = build_user_session(user.id)
    user_repo = AsyncMock()
    session_repo = AsyncMock()
    user_repo.get_by_id = AsyncMock(return_value=user)
    session_repo.get_by_token = AsyncMock(return_value=session)

    context = await authenticate_bearer_token(
        token,
        user_repository=user_repo,
        session_repository=session_repo,
        department_id=None,
    )

    assert context.user_id == user.id
    assert context.department_id == user.department_id
    assert context.email == user.email
    assert context.role == UserRole.SUPER_ADMIN
    user_repo.get_by_email_and_department.assert_not_awaited()


@pytest.mark.asyncio
async def test_authenticate_bearer_token_switches_auth_context_via_org_header(
    jwt_settings,
) -> None:
    login_dept_id = uuid4()
    other_dept_id = uuid4()
    session_user = _active_user(
        department_id=login_dept_id,
        email="ada@example.com",
        role=UserRole.NURSE,
    )
    other_membership = _active_user(
        department_id=other_dept_id,
        email="ada@example.com",
        role=UserRole.ADMIN,
    )
    token, _, session = build_user_session(session_user.id)
    user_repo = AsyncMock()
    session_repo = AsyncMock()
    user_repo.get_by_id = AsyncMock(return_value=session_user)
    user_repo.get_by_email_and_department = AsyncMock(return_value=other_membership)
    session_repo.get_by_token = AsyncMock(return_value=session)

    context = await authenticate_bearer_token(
        token,
        user_repository=user_repo,
        session_repository=session_repo,
        department_id=other_dept_id,
    )

    assert context.user_id == other_membership.id
    assert context.department_id == other_dept_id
    assert context.email == "ada@example.com"
    assert context.role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_authenticate_bearer_token_rejects_org_header_without_membership(
    jwt_settings,
) -> None:
    user = _active_user()
    token, _, session = build_user_session(user.id)
    user_repo = AsyncMock()
    session_repo = AsyncMock()
    user_repo.get_by_id = AsyncMock(return_value=user)
    user_repo.get_by_email_and_department = AsyncMock(return_value=None)
    session_repo.get_by_token = AsyncMock(return_value=session)

    with pytest.raises(ForbiddenError, match="do not have access"):
        await authenticate_bearer_token(
            token,
            user_repository=user_repo,
            session_repository=session_repo,
            department_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_authenticate_bearer_token_rejects_unknown_user(jwt_settings) -> None:
    user = _active_user()
    token, _, session = build_user_session(user.id)
    user_repo = AsyncMock()
    user_repo.get_by_id = AsyncMock(return_value=None)
    session_repo = AsyncMock()
    session_repo.get_by_token = AsyncMock(return_value=session)

    with pytest.raises(UnauthorizedError, match="Missing or invalid access token"):
        await authenticate_bearer_token(
            token, user_repository=user_repo, session_repository=session_repo
        )
