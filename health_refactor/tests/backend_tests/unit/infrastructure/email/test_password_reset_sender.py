"""Unit tests: infrastructure/email/password_reset_sender.py"""
import logging
from unittest.mock import AsyncMock

import pytest

from backend.src.infrastructure.email.password_reset_sender import PasswordResetEmailSender
from backend.src.infrastructure.email.types import EmailMessage


@pytest.mark.asyncio
async def test_send_password_reset_skipped_in_development_logs_link(
    monkeypatch, caplog
) -> None:
    monkeypatch.setattr(
        "backend.src.infrastructure.email.password_reset_sender.settings.app_env",
        "development",
    )
    monkeypatch.delenv("SEND_PASSWORD_RESET_EMAIL_IN_DEV", raising=False)
    caplog.set_level(
        logging.INFO, logger="backend.src.infrastructure.email.password_reset_sender"
    )
    template_sender = AsyncMock()
    sender = PasswordResetEmailSender(template_sender=template_sender)
    link = "http://localhost:3000/auth/reset-password?email=user%40example.com&token=secret"

    await sender.send_password_reset(to_email="user@example.com", reset_link=link)

    template_sender.send.assert_not_awaited()
    assert "password_reset_email: skipped" in caplog.text
    assert link in caplog.text


@pytest.mark.asyncio
async def test_send_password_reset_delegates_to_template_sender(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.src.infrastructure.email.password_reset_sender.settings.app_env",
        "production",
    )
    monkeypatch.setattr(
        "backend.src.infrastructure.email.password_reset_sender.settings.app_name",
        "SupportOS AI",
    )
    monkeypatch.setattr(
        "backend.src.infrastructure.email.password_reset_sender.settings.password_reset_expire_hours",
        2,
    )
    template_sender = AsyncMock()
    sender = PasswordResetEmailSender(template_sender=template_sender)
    link = "http://localhost:3000/auth/reset-password?email=user%40example.com&token=secret"

    await sender.send_password_reset(to_email="user@example.com", reset_link=link)

    template_sender.send.assert_awaited_once()
    call = template_sender.send.await_args.kwargs
    assert call["to"] == "user@example.com"
    assert call["template_name"] == "password_reset"
    assert call["context"]["reset_link"] == link
    assert call["context"]["expire_hours"] == 2
    assert "SupportOS AI" in call["subject"]


@pytest.mark.asyncio
async def test_send_password_reset_uses_template_and_provider(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.src.infrastructure.email.password_reset_sender.settings.app_env",
        "production",
    )
    monkeypatch.setattr(
        "backend.src.infrastructure.email.template_email_sender.settings.app_name",
        "SupportOS AI",
    )
    provider = AsyncMock()
    sender = PasswordResetEmailSender(email_provider=provider)
    link = "http://localhost:3000/auth/reset-password?email=user%40example.com&token=secret"

    await sender.send_password_reset(to_email="user@example.com", reset_link=link)

    provider.send.assert_awaited_once()
    message: EmailMessage = provider.send.await_args.args[0]
    assert message.to == "user@example.com"
    assert "SupportOS AI" in message.subject
    assert "secret" in message.html
    assert message.text is not None
    assert "secret" in message.text
