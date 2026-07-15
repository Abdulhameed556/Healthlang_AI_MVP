"""Use-case: exchange a refresh token for new access and refresh tokens."""
import logging
from datetime import datetime, timezone

from backend.src.application.auth.commands.refresh_token import RefreshTokenCommand
from backend.src.application.auth.results.refresh_token import RefreshTokenResult
from backend.src.application.auth.services.session_tokens import rotate_session_tokens
from backend.src.core.exceptions import ForbiddenError, UnauthorizedError
from backend.src.domain.auth.repositories import IUserSessionRepository
from backend.src.domain.users.repositories import IUserRepository
from backend.src.domain.users.value_objects import UserStatus

logger = logging.getLogger(__name__)


class RefreshToken:
    def __init__(
        self,
        user_repository: IUserRepository,
        session_repository: IUserSessionRepository,
    ) -> None:
        self._user_repository = user_repository
        self._session_repository = session_repository

    async def execute(self, command: RefreshTokenCommand) -> RefreshTokenResult:
        raw = command.refresh_token.strip()
        if not raw:
            raise UnauthorizedError("Missing or invalid refresh token")

        session = await self._session_repository.get_by_refresh_token(raw)
        if session is None:
            raise UnauthorizedError("Missing or invalid refresh token")

        now = datetime.now(timezone.utc)
        if session.refresh_expires_at is None or session.refresh_expires_at <= now:
            raise UnauthorizedError("Refresh token has expired")

        user = await self._user_repository.get_by_id(session.user_id)
        if user is None:
            raise UnauthorizedError("Missing or invalid refresh token")

        if user.status != UserStatus.ACTIVE:
            raise ForbiddenError("Account is not active")

        access_token, refresh_token, updated_session = rotate_session_tokens(session)
        await self._session_repository.save(updated_session)

        logger.info("refresh_token: success user_id=%s", user.id)
        return RefreshTokenResult(
            access_token=access_token,
            refresh_token=refresh_token,
        )
