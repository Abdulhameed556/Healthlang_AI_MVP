"""Domain entities for auth sessions."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class UserSession:
    id: UUID
    user_id: UUID
    token: str
    created_at: datetime
    expires_at: datetime
    refresh_token: str | None = None
    refresh_expires_at: datetime | None = None
    invalidated_at: datetime | None = None


@dataclass
class PasswordReset:
    id: UUID
    user_id: UUID
    otp_hash: str
    status: str
    expires_at: datetime
    created_at: datetime
    used_at: datetime | None = None
