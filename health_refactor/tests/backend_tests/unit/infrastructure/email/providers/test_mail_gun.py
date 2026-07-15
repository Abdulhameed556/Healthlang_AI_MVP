"""Unit tests: infrastructure/email/providers/mail_gun.py"""
from unittest.mock import AsyncMock

import httpx
import pytest

from backend.src.core.exceptions import EmailDeliveryError
from backend.src.infrastructure.email.providers.mail_gun import MailgunEmailProvider
from backend.src.infrastructure.email.types import EmailMessage


class _FakeAsyncClient:
    def __init__(self, response: httpx.Response) -> None:
        self._response = response
        self.post = AsyncMock(return_value=response)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None


@pytest.mark.asyncio
async def test_send_posts_to_mailgun_api(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.src.infrastructure.email.providers.mail_gun.settings.mailgun_api_key",
        "key-test",
    )
    monkeypatch.setattr(
        "backend.src.infrastructure.email.providers.mail_gun.settings.mailgun_domain",
        "mg.example.com",
    )
    monkeypatch.setattr(
        "backend.src.infrastructure.email.providers.mail_gun.settings.mailgun_api_base",
        "https://api.mailgun.net/v3",
    )
    monkeypatch.setattr(
        "backend.src.infrastructure.email.providers.mail_gun.settings.email_from",
        "noreply@mg.example.com",
    )

    fake_client = _FakeAsyncClient(httpx.Response(200, json={"message": "Queued"}))
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **_kwargs: fake_client,
    )

    provider = MailgunEmailProvider()
    await provider.send(
        EmailMessage(
            to="user@example.com",
            subject="Hello",
            html="<p>Hi</p>",
            text="Hi",
        )
    )

    fake_client.post.assert_awaited_once()
    call = fake_client.post.await_args
    assert call.kwargs["auth"] == ("api", "key-test")
    assert call.args[0] == "https://api.mailgun.net/v3/mg.example.com/messages"
    assert call.kwargs["data"]["to"] == "user@example.com"


@pytest.mark.asyncio
async def test_send_raises_email_delivery_error_on_mailgun_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.src.infrastructure.email.providers.mail_gun.settings.mailgun_api_key",
        "key-test",
    )
    monkeypatch.setattr(
        "backend.src.infrastructure.email.providers.mail_gun.settings.mailgun_domain",
        "mg.example.com",
    )
    monkeypatch.setattr(
        "backend.src.infrastructure.email.providers.mail_gun.settings.mailgun_api_base",
        "https://api.mailgun.net/v3",
    )

    fake_client = _FakeAsyncClient(httpx.Response(500, text="Server error"))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: fake_client)

    provider = MailgunEmailProvider()
    with pytest.raises(EmailDeliveryError, match="Mailgun send failed"):
        await provider.send(
            EmailMessage(to="user@example.com", subject="Hi", html="<p>x</p>")
        )


@pytest.mark.asyncio
async def test_send_falls_back_to_log_when_unconfigured(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.src.infrastructure.email.providers.mail_gun.settings.mailgun_api_key", ""
    )
    monkeypatch.setattr(
        "backend.src.infrastructure.email.providers.mail_gun.settings.mailgun_domain", ""
    )

    provider = MailgunEmailProvider()
    await provider.send(
        EmailMessage(to="user@example.com", subject="Hi", html="<p>x</p>")
    )
