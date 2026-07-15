"""Abstract repository interfaces for auth (Protocol)."""
from typing import Protocol
from uuid import UUID

from backend.src.domain.auth.entities import PasswordReset, UserSession


class IUserSessionRepository(Protocol):
    async def add(self, session: UserSession) -> UserSession:
        """Persist a new session."""
        ...

    async def get_by_token(self, token: str) -> UserSession | None:
        """Load a non-invalidated session by token, if any."""
        ...

    async def invalidate_by_token(self, token: str) -> None:
        """Mark session invalidated (logout)."""
        ...

    async def invalidate_all_for_user(self, user_id: UUID) -> None:
        """Invalidate every active session for a user."""
        ...


class IPasswordResetRepository(Protocol):
    async def add(self, password_reset: PasswordReset) -> PasswordReset:
        """Persist a new password reset request."""
        ...

    async def save(self, password_reset: PasswordReset) -> PasswordReset:
        """Update a password reset row."""
        ...

    async def list_pending_for_user_ids(
        self, user_ids: list[UUID]
    ) -> list[PasswordReset]:
        """Load pending resets for the given users."""
        ...

    async def expire_pending_for_user(self, user_id: UUID) -> None:
        """Mark all pending resets for a user as expired."""
        ...
