"""Use-case: request password reset link by email."""
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.src.application.auth.commands.request_password_reset import (
    RequestPasswordResetCommand,
)
from backend.src.application.auth.ports.password_reset_email import IPasswordResetEmailSender
from backend.src.application.auth.results.password_reset import RequestPasswordResetResult
from backend.src.application.auth.services.password_reset_tokens import (
    build_password_reset_link,
    generate_password_reset_token,
)
from backend.src.application.auth.services.password_reset_user_resolution import (
    resolve_user_for_password_reset,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.core.config import settings
from backend.src.core.security import hash_password
from backend.src.domain.auth.entities import PasswordReset
from backend.src.domain.auth.repositories import IPasswordResetRepository
from backend.src.domain.auth.value_objects import PasswordResetStatus
from backend.src.domain.users.repositories import IUserRepository
from backend.src.infrastructure.repositories._utils import normalize_email

logger = logging.getLogger(__name__)


class RequestPasswordReset:
    def __init__(
        self,
        user_repository: IUserRepository,
        password_reset_repository: IPasswordResetRepository,
        password_reset_email_sender: IPasswordResetEmailSender,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._user_repository = user_repository
        self._password_reset_repository = password_reset_repository
        self._password_reset_email_sender = password_reset_email_sender
        self._unit_of_work = unit_of_work

    async def execute(
        self, command: RequestPasswordResetCommand
    ) -> RequestPasswordResetResult:
        email = normalize_email(command.email)
        users = await self._user_repository.list_by_email(email)
        user = resolve_user_for_password_reset(users)
        if user is None:
            logger.info("password_reset_request: no eligible user email=%s", email)
            return RequestPasswordResetResult(reset_link=None)

        token = generate_password_reset_token()
        now = datetime.now(timezone.utc)
        await self._password_reset_repository.expire_pending_for_user(user.id)
        await self._password_reset_repository.add(
            PasswordReset(
                id=uuid4(),
                user_id=user.id,
                otp_hash=hash_password(token),
                status=PasswordResetStatus.PENDING.value,
                expires_at=now
                + timedelta(hours=settings.password_reset_expire_hours),
                created_at=now,
            )
        )
        reset_link = build_password_reset_link(email, token)
        await self._password_reset_email_sender.send_password_reset(
            to_email=email,
            reset_link=reset_link,
        )
        await self._unit_of_work.commit()
        logger.info("password_reset_request: sent email=%s user_id=%s", email, user.id)
        expose_reset_link = not settings.send_password_reset_email
        return RequestPasswordResetResult(
            reset_link=reset_link if expose_reset_link else None,
        )
