"""Unit tests: infrastructure/email/template_email_sender.py"""
import logging
from unittest.mock import AsyncMock

import pytest

from backend.src.infrastructure.email.template_email_sender import TemplateEmailSender
from backend.src.infrastructure.email.types import EmailMessage


@pytest.mark.asyncio
async def test_send_renders_template_by_name_and_variables() -> None:
    provider = AsyncMock()
    sender = TemplateEmailSender(email_provider=provider)

    await sender.send(
        to="user@example.com",
        subject="Hello",
        template_name="invitation",
        context={
            "app_name": "SupportOS AI",
            "department_name": "Acme",
            "invitation_link": "http://localhost/accept?token=secret",
            "expire_hours": 48,
        },
    )

    provider.send.assert_awaited_once()
    message: EmailMessage = provider.send.await_args.args[0]
    assert message.to == "user@example.com"
    assert message.subject == "Hello"
    assert "Acme" in message.html
    assert message.text is not None
    assert "secret" in message.text


@pytest.mark.asyncio
async def test_send_logs_template_name(caplog) -> None:
    caplog.set_level(logging.INFO, logger="backend.src.infrastructure.email.template_email_sender")
    provider = AsyncMock()
    sender = TemplateEmailSender(email_provider=provider)

    await sender.send(
        to="user@example.com",
        subject="Hi",
        template_name="invitation",
        context={
            "app_name": "SupportOS AI",
            "department_name": "Acme",
            "invitation_link": "http://localhost/accept?token=x",
            "expire_hours": 24,
        },
    )

    assert "template=invitation" in caplog.text
