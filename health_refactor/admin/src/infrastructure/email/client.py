"""
Mailgun email sender (async).

The Admin Panel sends transactional email (e.g. login OTP) through
Mailgun's HTTP API using ``httpx`` so the call never blocks the event loop.

In development, if Mailgun credentials are not configured we log the
message and return without raising — this keeps local login working (the
OTP is the fixed dev code ``123456``) without a real Mailgun account.
"""
from __future__ import annotations

import logging

import httpx

from admin.src.core.config import settings
from admin.src.core.exceptions import AppError
from admin.src.infrastructure.email.templates import (
    invite_admin_user_email,
    otp_login_email,
)

logger = logging.getLogger(__name__)

_MAILGUN_TIMEOUT = 10.0


class EmailClient:
    def __init__(self) -> None:
        self._domain = settings.mailgun_api_domain
        self._api_key = settings.mailgun_api_key
        self._from = settings.email_from

    def _configured(self) -> bool:
        return bool(self._domain and self._api_key)

    async def send(
        self,
        to_email: str,
        subject: str,
        text: str,
        html: str | None = None,
    ) -> None:
        """Send one email via Mailgun. Raises AppError on failure."""
        if not self._configured():
            if settings.app_env == "development":
                logger.warning(
                    "Mailgun not configured; skipping email to %s (%r)",
                    to_email,
                    subject,
                )
                return
            raise AppError("Email service is not configured")

        url = f"https://api.mailgun.net/v3/{self._domain}/messages"
        data = {
            "from": self._from,
            "to": to_email,
            "subject": subject,
            "text": text,
        }
        if html:
            data["html"] = html

        try:
            async with httpx.AsyncClient(timeout=_MAILGUN_TIMEOUT) as client:
                response = await client.post(
                    url, auth=("api", self._api_key), data=data
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Failed to send email to %s: %s", to_email, exc)
            raise AppError("Failed to send email") from exc

    async def send_otp_email(self, to_email: str, otp: str) -> None:
        """Send the login OTP code to an admin's email."""
        body = otp_login_email(otp)
        await self.send(
            to_email, body["subject"], body["text"], body["html"]
        )

    async def send_invite_email(self, to_email: str, invite_link: str, role: str) -> None:
        """Send a new Admin Panel user their invitation link."""
        body = invite_admin_user_email(invite_link, role)
        await self.send(
            to_email, body["subject"], body["text"], body["html"]
        )
