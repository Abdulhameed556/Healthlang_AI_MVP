"""Use-case: set a new password using a reset token."""
import logging
from datetime import datetime, timezone

from backend.src.application.auth.commands.complete_password_reset import (
    CompletePasswordResetCommand,
)
from backend.src.application.auth.results.password_reset import CompletePasswordResetResult
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.core.security import hash_password, verify_password
from backend.src.domain.auth.exceptions import InvalidPasswordResetError
from backend.src.domain.auth.repositories import (
    IPasswordResetRepository,
    IUserSessionRepository,
)
from backend.src.domain.auth.value_objects import PasswordResetStatus
from backend.src.domain.users.repositories import IUserRepository
from backend.src.infrastructure.repositories._utils import normalize_email

logger = logging.getLogger(__name__)

_INVALID_RESET_MESSAGE = "Invalid or expired password reset link"


class CompletePasswordReset:
    def __init__(
        self,
        user_repository: IUserRepository,
        password_reset_repository: IPasswordResetRepository,
        session_repository: IUserSessionRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._user_repository = user_repository
        self._password_reset_repository = password_reset_repository
        self._session_repository = session_repository
        self._unit_of_work = unit_of_work

    async def execute(
        self, command: CompletePasswordResetCommand
    ) -> CompletePasswordResetResult:
        email = normalize_email(command.email)
        token = command.token.strip()
        if not token:
            raise InvalidPasswordResetError(_INVALID_RESET_MESSAGE)

        users = await self._user_repository.list_by_email(email)
        if not users:
            raise InvalidPasswordResetError(_INVALID_RESET_MESSAGE)

        user_ids = [user.id for user in users]
        pending_resets = await self._password_reset_repository.list_pending_for_user_ids(
            user_ids
        )
        now = datetime.now(timezone.utc)
        matched_reset = None
        matched_user = None
        for password_reset in pending_resets:
            if password_reset.expires_at <= now:
                password_reset.status = PasswordResetStatus.EXPIRED.value
                await self._password_reset_repository.save(password_reset)
                continue
            if not verify_password(token, password_reset.otp_hash):
                continue
            matched_reset = password_reset
            matched_user = next(
                (user for user in users if user.id == password_reset.user_id),
                None,
            )
            break

        if matched_reset is None or matched_user is None:
            raise InvalidPasswordResetError(_INVALID_RESET_MESSAGE)

        matched_user.password_hash = hash_password(command.new_password)
        matched_user.updated_at = now
        await self._user_repository.save(matched_user)

        matched_reset.status = PasswordResetStatus.USED.value
        matched_reset.used_at = now
        await self._password_reset_repository.save(matched_reset)
        await self._session_repository.invalidate_all_for_user(matched_user.id)
        await self._unit_of_work.commit()

        logger.info(
            "password_reset_complete: success user_id=%s email=%s",
            matched_user.id,
            email,
        )
        return CompletePasswordResetResult()
