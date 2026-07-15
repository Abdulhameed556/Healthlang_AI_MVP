"""Result: member removed from department."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RemoveDepartmentMemberResult:
    user_id: UUID
