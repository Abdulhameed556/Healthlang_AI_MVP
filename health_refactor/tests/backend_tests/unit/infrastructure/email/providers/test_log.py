"""Unit tests: infrastructure/email/providers/log.py"""
import logging

import pytest

from backend.src.infrastructure.email.providers.log import LogEmailProvider
from backend.src.infrastructure.email.types import EmailMessage


@pytest.mark.asyncio
async def test_log_provider_logs_recipient_and_subject(caplog) -> None:
    caplog.set_level(logging.INFO, logger="backend.src.infrastructure.email.providers.log")

    await LogEmailProvider().send(
        EmailMessage(
            to="user@example.com",
            subject="Test subject",
            html="<p>Hi</p>",
            text="Hi",
        )
    )

    assert "user@example.com" in caplog.text
    assert "Test subject" in caplog.text
