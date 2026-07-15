"""Commands for listing department members."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ListDepartmentUsersCommand:
    department_id: UUID
    page: int = 1
    page_size: int = 20
