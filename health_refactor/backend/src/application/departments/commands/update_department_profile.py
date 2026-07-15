"""Commands for updating department profile."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UpdateDepartmentProfileCommand:
    department_id: UUID
    name: str | None = None
    description: str | None = None
