"""Unit tests: infrastructure/email/providers/smtp.py"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.src.infrastructure.email.providers.smtp import SmtpEmailProvider
from backend.src.infrastructure.email.types import EmailMessage


@pytest.mark.asyncio
async def test_smtp_falls_back_to_log_when_host_unset(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.src.infrastructure.email.providers.smtp.settings.smtp_host", ""
    )
    log_instance = MagicMock()
    log_instance.send = AsyncMock()
    log_cls = MagicMock(return_value=log_instance)
    monkeypatch.setattr(
        "backend.src.infrastructure.email.providers.log.LogEmailProvider",
        log_cls,
    )

    await SmtpEmailProvider().send(
        EmailMessage(to="user@example.com", subject="Hi", html="<p>x</p>")
    )

    log_cls.assert_called_once()
    log_instance.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_smtp_send_sync_called_when_host_configured(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.src.infrastructure.email.providers.smtp.settings.smtp_host", "smtp.example.com"
    )
    monkeypatch.setattr("backend.src.infrastructure.email.providers.smtp.settings.smtp_port", 587)
    monkeypatch.setattr("backend.src.infrastructure.email.providers.smtp.settings.smtp_user", "")
    provider = SmtpEmailProvider()
    message = EmailMessage(to="user@example.com", subject="Hi", html="<p>x</p>")

    with patch.object(provider, "_send_sync", MagicMock()) as send_sync:
        with patch(
            "backend.src.infrastructure.email.providers.smtp.asyncio.to_thread",
            new=AsyncMock(return_value=None),
        ) as to_thread:
            await provider.send(message)
            to_thread.assert_awaited_once_with(send_sync, message)
