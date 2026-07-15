"""Domain entities for departments."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class Department:
    id: UUID
    name: str
    status: str
    created_at: datetime
    description: str | None = None
