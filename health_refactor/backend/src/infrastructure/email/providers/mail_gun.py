"""Mailgun HTTP API email provider."""
import logging

import httpx

from backend.src.core.config import settings
from backend.src.core.exceptions import EmailDeliveryError
from backend.src.infrastructure.email.providers.base import IEmailProvider
from backend.src.infrastructure.email.registry import register_provider
from backend.src.infrastructure.email.types import EmailMessage

logger = logging.getLogger(__name__)


class MailgunEmailProvider:
    async def send(self, message: EmailMessage) -> None:
        if not settings.mailgun_api_key or not settings.mailgun_domain:
            logger.warning(
                "MAILGUN_API_KEY or MAILGUN_DOMAIN not set; falling back to log for to=%s",
                message.to,
            )
            from backend.src.infrastructure.email.providers.log import LogEmailProvider

            await LogEmailProvider().send(message)
            return

        from_addr = message.from_address or settings.email_from
        url = (
            f"{settings.mailgun_api_base.rstrip('/')}/"
            f"{settings.mailgun_domain}/messages"
        )

        data: dict[str, str] = {
            "from": from_addr,
            "to": message.to,
            "subject": message.subject,
            "html": message.html,
        }
        if message.text:
            data["text"] = message.text

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                auth=("api", settings.mailgun_api_key),
                data=data,
            )

        if response.status_code != 200:
            raise EmailDeliveryError(
                f"Mailgun send failed ({response.status_code}): {response.text}"
            )

        logger.info(
            "Email sent via Mailgun to=%s subject=%s",
            message.to,
            message.subject,
        )


@register_provider("mailgun")
def create_mailgun_email_provider() -> IEmailProvider:
    return MailgunEmailProvider()
