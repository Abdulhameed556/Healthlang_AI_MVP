"""SMTP email provider."""
import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.src.core.config import settings
from backend.src.infrastructure.email.providers.base import IEmailProvider
from backend.src.infrastructure.email.registry import register_provider
from backend.src.infrastructure.email.types import EmailMessage

logger = logging.getLogger(__name__)


class SmtpEmailProvider:
    async def send(self, message: EmailMessage) -> None:
        if not settings.smtp_host:
            logger.warning(
                "SMTP_HOST not set; falling back to log-only for to=%s",
                message.to,
            )
            from backend.src.infrastructure.email.providers.log import LogEmailProvider

            await LogEmailProvider().send(message)
            return
        await asyncio.to_thread(self._send_sync, message)

    def _send_sync(self, message: EmailMessage) -> None:
        from_addr = message.from_address or settings.email_from
        multipart = MIMEMultipart("alternative")
        multipart["Subject"] = message.subject
        multipart["From"] = from_addr
        multipart["To"] = message.to

        if message.text:
            multipart.attach(MIMEText(message.text, "plain", "utf-8"))
        multipart.attach(MIMEText(message.html, "html", "utf-8"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as client:
            if settings.smtp_user:
                client.starttls()
                client.login(settings.smtp_user, settings.smtp_password)
            client.sendmail(from_addr, [message.to], multipart.as_string())

        logger.info("Email sent via SMTP to=%s subject=%s", message.to, message.subject)


@register_provider("smtp")
def create_smtp_email_provider() -> IEmailProvider:
    return SmtpEmailProvider()
