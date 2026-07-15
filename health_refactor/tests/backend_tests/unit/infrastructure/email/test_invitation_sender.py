"""Unit tests: infrastructure/email/invitation_sender.py"""
import logging
from unittest.mock import AsyncMock

import pytest

from backend.src.infrastructure.email.invitation_sender import InvitationEmailSender
from backend.src.infrastructure.email.types import EmailMessage


@pytest.mark.asyncio
async def test_send_invitation_skipped_in_development_logs_link(
    monkeypatch, caplog
) -> None:
    monkeypatch.setattr(
        "backend.src.infrastructure.email.invitation_sender.settings.app_env",
        "development",
    )
    monkeypatch.delenv("SEND_INVITATION_EMAIL_IN_DEV", raising=False)
    caplog.set_level(logging.INFO, logger="backend.src.infrastructure.email.invitation_sender")
    template_sender = AsyncMock()
    sender = InvitationEmailSender(template_sender=template_sender)
    link = (
        "http://localhost:3000/invite?dept=Acme+Corp"
        "&user_email=admin%40example.com&token=secret"
    )

    await sender.send_invitation(
        to_email="admin@example.com",
        invitation_link=link,
        department_name="Acme Corp",
    )

    template_sender.send.assert_not_awaited()
    assert "invitation_email: skipped" in caplog.text
    assert link in caplog.text


@pytest.mark.asyncio
async def test_send_invitation_delegates_to_template_sender(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.src.infrastructure.email.invitation_sender.settings.app_env",
        "production",
    )
    template_sender = AsyncMock()
    sender = InvitationEmailSender(template_sender=template_sender)

    await sender.send_invitation(
        to_email="admin@example.com",
        invitation_link=(
            "http://localhost:3000/invite?dept=Acme+Corp"
            "&user_email=admin%40example.com&token=secret"
        ),
        department_name="Acme Corp",
    )

    template_sender.send.assert_awaited_once()
    call = template_sender.send.await_args.kwargs
    assert call["to"] == "admin@example.com"
    assert call["template_name"] == "invitation"
    assert call["context"]["department_name"] == "Acme Corp"
    assert "secret" in call["context"]["invitation_link"]


@pytest.mark.asyncio
async def test_send_invitation_uses_template_and_provider(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.src.infrastructure.email.invitation_sender.settings.app_env",
        "production",
    )
    monkeypatch.setattr(
        "backend.src.infrastructure.email.template_email_sender.settings.app_name",
        "SupportOS AI",
    )
    provider = AsyncMock()
    sender = InvitationEmailSender(email_provider=provider)

    await sender.send_invitation(
        to_email="admin@example.com",
        invitation_link=(
            "http://localhost:3000/invite?dept=Acme+Corp"
            "&user_email=admin%40example.com&token=secret"
        ),
        department_name="Acme Corp",
    )

    provider.send.assert_awaited_once()
    message: EmailMessage = provider.send.await_args.args[0]
    assert message.to == "admin@example.com"
    assert "Acme Corp" in message.subject
    assert "SupportOS AI" in message.subject
    assert "Acme Corp" in message.html
    assert "secret" in message.html
    assert message.text is not None
    assert "secret" in message.text


@pytest.mark.asyncio
async def test_send_invitation_logs_provider(monkeypatch, caplog) -> None:
    monkeypatch.setattr(
        "backend.src.infrastructure.email.invitation_sender.settings.app_env",
        "production",
    )
    caplog.set_level(logging.INFO, logger="backend.src.infrastructure.email.invitation_sender")
    provider = AsyncMock()
    sender = InvitationEmailSender(email_provider=provider)

    await sender.send_invitation(
        to_email="admin@example.com",
        invitation_link=(
            "http://localhost:3000/invite?dept=Acme+Corp"
            "&user_email=admin%40example.com&token=secret"
        ),
        department_name="Acme Corp",
    )

    assert "invitation_email: sending" in caplog.text
    assert "template=invitation" in caplog.text
    assert "admin@example.com" in caplog.text
