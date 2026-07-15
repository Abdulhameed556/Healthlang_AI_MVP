"""Results for department profile."""
from dataclasses import dataclass
from uuid import UUID

from backend.src.domain.departments.value_objects import DepartmentStatus


@dataclass(frozen=True)
class GetDepartmentProfileResult:
    department_id: UUID
    name: str
    description: str | None
    status: DepartmentStatus
