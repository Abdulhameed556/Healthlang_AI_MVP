"""Commands for the department dashboard."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetDepartmentDashboardCommand:
    department_id: UUID
