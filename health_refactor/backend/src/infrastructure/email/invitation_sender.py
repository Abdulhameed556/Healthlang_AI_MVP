"""Send SupportOS AI invitation emails via template name + variables."""
import logging

from backend.src.application.users.ports.email import IInvitationEmailSender
from backend.src.core.config import settings
from backend.src.infrastructure.email.providers.base import IEmailProvider
from backend.src.infrastructure.email.template_email_sender import TemplateEmailSender

logger = logging.getLogger(__name__)

INVITATION_TEMPLATE = "invitation"


class InvitationEmailSender(IInvitationEmailSender):
    def __init__(
        self,
        email_provider: IEmailProvider | None = None,
        template_sender: TemplateEmailSender | None = None,
    ) -> None:
        self._template_sender = template_sender or TemplateEmailSender(email_provider)

    async def send_invitation(
        self,
        *,
        to_email: str,
        invitation_link: str,
        department_name: str,
    ) -> None:
        if not settings.send_invitation_email:
            logger.info(
                "invitation_email: skipped (APP_ENV=%s) to=%s department=%s "
                "invitation_link=%s",
                settings.app_env,
                to_email,
                department_name,
                invitation_link,
            )
            return

        app_name = settings.app_name
        context = {
            "app_name": app_name,
            "department_name": department_name,
            "invitation_link": invitation_link,
            "expire_hours": settings.invitation_expire_hours,
        }

        logger.info(
            "invitation_email: sending to=%s department=%s template=%s",
            to_email,
            department_name,
            INVITATION_TEMPLATE,
        )
        await self._template_sender.send(
            to=to_email,
            subject=f"You're invited to {department_name} on {app_name}",
            template_name=INVITATION_TEMPLATE,
            context=context,
        )
        logger.info("invitation_email: sent to=%s", to_email)
