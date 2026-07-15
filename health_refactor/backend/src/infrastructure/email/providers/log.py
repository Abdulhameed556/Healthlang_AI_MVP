"""Log-only email provider for local development."""
import logging

from backend.src.infrastructure.email.providers.base import IEmailProvider
from backend.src.infrastructure.email.registry import register_provider
from backend.src.infrastructure.email.types import EmailMessage

logger = logging.getLogger(__name__)


class LogEmailProvider:
    async def send(self, message: EmailMessage) -> None:
        logger.info(
            "Email (log provider) to=%s subject=%s",
            message.to,
            message.subject,
        )
        if message.text:
            logger.debug("Plain text body:\n%s", message.text)
        logger.debug("HTML body:\n%s", message.html)


@register_provider("log")
def create_log_email_provider() -> IEmailProvider:
    return LogEmailProvider()
