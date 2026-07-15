"""Domain entities for invitations."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Invitation:
    id: UUID
    department_id: UUID
    email: str
    role: str
    token: str
    status: str
    expires_at: datetime
    created_at: datetime
    invited_by: UUID | None = None
    accepted_at: datetime | None = None
