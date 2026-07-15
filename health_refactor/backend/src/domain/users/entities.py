"""Domain entities for users."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    id: UUID
    department_id: UUID
    first_name: str
    last_name: str
    email: str
    role: str
    status: str
    auth_method: str
    created_at: datetime
    updated_at: datetime
    password_hash: str | None = None
