"""Abstract repository interfaces for users (Protocol)."""
from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from backend.src.domain.users.entities import User


class IUserRepository(Protocol):
    async def add(self, user: User) -> User:
        """Persist a new user."""
        ...

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Load user by primary key."""
        ...

    async def get_by_email(self, email: str) -> User | None:
        """Load a user by email (first match)."""
        ...

    async def list_by_email(self, email: str) -> list[User]:
        """Load every user row for an email across departments."""
        ...

    async def get_by_email_and_department(
        self, email: str, department_id: UUID
    ) -> User | None:
        """Load user membership for an email within one department."""
        ...

    async def exists_by_email(self, email: str) -> bool:
        """Return True if any user already uses this email."""
        ...

    async def save(self, user: User) -> User:
        """Insert or update a user."""
        ...

    async def list_by_department_id(
        self,
        department_id: UUID,
        *,
        page: int,
        page_size: int,
        statuses: Sequence[str] | None = None,
    ) -> tuple[list[User], int]:
        """List users in a department with pagination, optionally filtered by status."""
        ...
