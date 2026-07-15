"""Auth domain entities."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class AdminSession:
    id: UUID
    user_id: UUID
    token: str
    created_at: datetime
    expires_at: datetime
    invalidated_at: datetime | None = None


@dataclass
class AdminInvitation:
    id: UUID
    email: str
    role: str
    token: str
    invited_by: UUID | None
    status: str          # pending | accepted | expired | revoked
    expires_at: datetime
    accepted_at: datetime | None
    created_at: datetime
