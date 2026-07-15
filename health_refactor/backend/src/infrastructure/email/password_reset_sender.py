"""Send password reset emails via template name + variables."""
import logging

from backend.src.application.auth.ports.password_reset_email import IPasswordResetEmailSender
from backend.src.core.config import settings
from backend.src.infrastructure.email.providers.base import IEmailProvider
from backend.src.infrastructure.email.template_email_sender import TemplateEmailSender

logger = logging.getLogger(__name__)

PASSWORD_RESET_TEMPLATE = "password_reset"


class PasswordResetEmailSender(IPasswordResetEmailSender):
    def __init__(
        self,
        email_provider: IEmailProvider | None = None,
        template_sender: TemplateEmailSender | None = None,
    ) -> None:
        self._template_sender = template_sender or TemplateEmailSender(email_provider)

    async def send_password_reset(
        self,
        *,
        to_email: str,
        reset_link: str,
    ) -> None:
        if not settings.send_password_reset_email:
            logger.info(
                "password_reset_email: skipped (APP_ENV=%s) to=%s reset_link=%s",
                settings.app_env,
                to_email,
                reset_link,
            )
            return

        app_name = settings.app_name
        context = {
            "app_name": app_name,
            "reset_link": reset_link,
            "expire_hours": settings.password_reset_expire_hours,
        }

        logger.info(
            "password_reset_email: sending to=%s template=%s",
            to_email,
            PASSWORD_RESET_TEMPLATE,
        )
        await self._template_sender.send(
            to=to_email,
            subject=f"Reset your {app_name} password",
            template_name=PASSWORD_RESET_TEMPLATE,
            context=context,
        )
        logger.info("password_reset_email: sent to=%s", to_email)
