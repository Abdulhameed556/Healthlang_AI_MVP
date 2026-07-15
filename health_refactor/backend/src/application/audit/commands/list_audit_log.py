"""Commands for listing the audit log."""
from dataclasses import dataclass
from uuid import UUID

from backend.src.domain.users.value_objects import UserRole


@dataclass(frozen=True)
class ListAuditLogCommand:
    viewer_role: UserRole
    viewer_department_id: UUID
    page: int = 1
    page_size: int = 20
