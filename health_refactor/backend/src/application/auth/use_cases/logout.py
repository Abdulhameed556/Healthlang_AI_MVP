"""Use-case: invalidate the current Bearer session (logout)."""
import logging

from backend.src.application.auth.commands.logout import LogoutCommand
from backend.src.domain.auth.repositories import IUserSessionRepository

logger = logging.getLogger(__name__)


class Logout:
    def __init__(self, session_repository: IUserSessionRepository) -> None:
        self._session_repository = session_repository

    async def execute(self, command: LogoutCommand) -> None:
        token = command.access_token.strip()
        await self._session_repository.invalidate_by_token(token)
        logger.info("logout: session invalidated")
