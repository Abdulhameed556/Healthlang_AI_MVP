"""Unit tests: Mailgun email client + OTP template."""
import httpx
import pytest
import respx

from admin.src.core.config import settings
from admin.src.core.exceptions import AppError
from admin.src.infrastructure.email.client import EmailClient
from admin.src.infrastructure.email.templates import otp_login_email

_MAILGUN = "https://api.mailgun.net/v3/mg.example.com/messages"


def _configure(monkeypatch, *, domain="mg.example.com", key="key-abc"):
    monkeypatch.setattr(settings, "mailgun_api_domain", domain)
    monkeypatch.setattr(settings, "mailgun_api_key", key)
    monkeypatch.setattr(settings, "email_from", "admin@platform.com")


class TestOtpTemplate:
    def test_contains_code_and_expiry(self):
        body = otp_login_email("123456")
        assert body["subject"]
        assert "123456" in body["text"]
        assert "10 minutes" in body["text"]
        assert "123456" in body["html"]


class TestEmailClient:
    @respx.mock
    async def test_send_otp_posts_to_mailgun(self, monkeypatch):
        _configure(monkeypatch)
        route = respx.post(_MAILGUN).mock(
            return_value=httpx.Response(200, json={"id": "1"})
        )
        await EmailClient().send_otp_email("admin@example.com", "123456")
        assert route.called
        request = route.calls[0].request
        assert b"123456" in request.content
        assert request.headers["Authorization"].startswith("Basic ")

    @respx.mock
    async def test_http_error_raises_apperror(self, monkeypatch):
        _configure(monkeypatch)
        respx.post(_MAILGUN).mock(return_value=httpx.Response(500, text="x"))
        with pytest.raises(AppError):
            await EmailClient().send_otp_email("admin@example.com", "123456")

    async def test_dev_unconfigured_skips_silently(self, monkeypatch):
        _configure(monkeypatch, domain="", key="")
        monkeypatch.setattr(settings, "app_env", "development")
        await EmailClient().send_otp_email("admin@example.com", "123456")

    async def test_prod_unconfigured_raises(self, monkeypatch):
        _configure(monkeypatch, domain="", key="")
        monkeypatch.setattr(settings, "app_env", "production")
        with pytest.raises(AppError):
            await EmailClient().send("a@b.com", "s", "t")
