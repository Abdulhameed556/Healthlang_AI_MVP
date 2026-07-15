"""Unit tests: application/auth/use_cases/request_password_reset.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.commands.request_password_reset import (
    RequestPasswordResetCommand,
)
from backend.src.application.auth.use_cases.request_password_reset import (
    RequestPasswordReset,
)
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


@pytest.fixture()
def use_case() -> RequestPasswordReset:
    user_repo = AsyncMock()
    password_reset_repo = AsyncMock()
    email_sender = AsyncMock()
    unit_of_work = AsyncMock()
    unit_of_work.commit = AsyncMock()
    password_reset_repo.add = AsyncMock(side_effect=lambda item: item)
    password_reset_repo.expire_pending_for_user = AsyncMock()
    email_sender.send_password_reset = AsyncMock()
    return RequestPasswordReset(
        user_repository=user_repo,
        password_reset_repository=password_reset_repo,
        password_reset_email_sender=email_sender,
        unit_of_work=unit_of_work,
    )


def _active_user(email: str = "user@example.com") -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid4(),
        department_id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email=email,
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE.value,
        auth_method=UserAuthMethod.EMAIL_PASSWORD.value,
        created_at=now,
        updated_at=now,
        password_hash="hash",
    )


@pytest.mark.asyncio
async def test_request_password_reset_sends_email_for_eligible_user(
    use_case: RequestPasswordReset,
    monkeypatch,
) -> None:
    user = _active_user()
    use_case._user_repository.list_by_email = AsyncMock(return_value=[user])
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.request_password_reset.settings.app_env",
        "production",
    )
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.request_password_reset.hash_password",
        lambda token: f"hashed:{token}",
    )
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.request_password_reset.generate_password_reset_token",
        lambda: "plain-token",
    )
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.request_password_reset.build_password_reset_link",
        lambda email, token: f"https://app.test/reset?email={email}&token={token}",
    )

    result = await use_case.execute(
        RequestPasswordResetCommand(email="user@example.com")
    )

    assert "account exists" in result.message
    assert result.reset_link is None
    use_case._password_reset_repository.add.assert_awaited_once()
    use_case._password_reset_email_sender.send_password_reset.assert_awaited_once()
    use_case._unit_of_work.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_request_password_reset_returns_reset_link_when_email_disabled(
    use_case: RequestPasswordReset,
    monkeypatch,
) -> None:
    user = _active_user()
    use_case._user_repository.list_by_email = AsyncMock(return_value=[user])
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.request_password_reset.settings.app_env",
        "development",
    )
    monkeypatch.delenv("SEND_PASSWORD_RESET_EMAIL_IN_DEV", raising=False)
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.request_password_reset.hash_password",
        lambda token: f"hashed:{token}",
    )
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.request_password_reset.generate_password_reset_token",
        lambda: "plain-token",
    )
    monkeypatch.setattr(
        "backend.src.application.auth.use_cases.request_password_reset.build_password_reset_link",
        lambda email, token: f"https://app.test/reset?email={email}&token={token}",
    )

    result = await use_case.execute(
        RequestPasswordResetCommand(email="user@example.com")
    )

    assert result.reset_link == "https://app.test/reset?email=user@example.com&token=plain-token"


@pytest.mark.asyncio
async def test_request_password_reset_returns_generic_message_when_no_user(
    use_case: RequestPasswordReset,
) -> None:
    use_case._user_repository.list_by_email = AsyncMock(return_value=[])

    result = await use_case.execute(
        RequestPasswordResetCommand(email="missing@example.com")
    )

    assert "account exists" in result.message
    use_case._password_reset_email_sender.send_password_reset.assert_not_awaited()
    use_case._unit_of_work.commit.assert_not_awaited()
