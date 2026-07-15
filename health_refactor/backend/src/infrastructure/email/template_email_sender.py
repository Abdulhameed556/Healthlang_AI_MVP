"""Send email using a template name and context variables (no per-email Python modules)."""
import logging
from typing import Any

from backend.src.core.config import settings
from backend.src.infrastructure.email.providers.base import IEmailProvider
from backend.src.infrastructure.email.registry import get_email_provider
from backend.src.infrastructure.email.templates import render_template, render_text_template
from backend.src.infrastructure.email.types import EmailMessage

logger = logging.getLogger(__name__)


class TemplateEmailSender:
    """Renders ``{template_name}.html`` / ``.txt`` and sends via the configured provider."""

    def __init__(self, email_provider: IEmailProvider | None = None) -> None:
        self._email_provider = email_provider or get_email_provider()
        self._provider_name = settings.email_provider
        self._provider_impl = type(self._email_provider).__name__

    async def send(
        self,
        *,
        to: str,
        subject: str,
        template_name: str,
        context: dict[str, Any],
        from_address: str | None = None,
    ) -> None:
        html = render_template(template_name, **context)
        text = render_text_template(template_name, **context)

        logger.info(
            "template_email: sending to=%s template=%s provider=%s impl=%s",
            to,
            template_name,
            self._provider_name,
            self._provider_impl,
        )
        await self._email_provider.send(
            EmailMessage(
                to=to,
                subject=subject,
                html=html,
                text=text,
                from_address=from_address or settings.email_from,
            )
        )
        logger.info(
            "template_email: sent to=%s template=%s subject=%s",
            to,
            template_name,
            subject,
        )
