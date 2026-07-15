"""Authenticated caller context for protected product routes."""
from dataclasses import dataclass
from uuid import UUID

from backend.src.domain.users.value_objects import UserRole


@dataclass(frozen=True)
class AuthContext:
    """Tenant-scoped caller identity for protected product routes.

    ``department_id`` is the active org for this request (login session org, or the
    org selected via ``X-Department-Id`` when the user belongs to multiple).
    """

    user_id: UUID
    department_id: UUID
    email: str
    role: UserRole
