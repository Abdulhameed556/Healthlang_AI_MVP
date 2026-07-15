"""Use-case: Logout — invalidate the caller's current session.

The raw JWT is hashed and matched against ``admin_sessions.token``; the row's
``invalidated_at`` is stamped so the token is rejected on subsequent requests
even though it has not yet reached its natural expiry.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from admin.src.core.security import hash_token

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from admin.src.domain.auth.repositories import IAdminSessionRepository


class LogoutUseCase:
    def __init__(
        self,
        session: AsyncSession,
        session_repo: IAdminSessionRepository,
    ) -> None:
        self._session = session
        self._sessions = session_repo

    async def execute(self, token: str) -> None:
        await self._sessions.invalidate(hash_token(token))
        await self._session.commit()
