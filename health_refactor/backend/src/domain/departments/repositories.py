"""Abstract repository interfaces for departments (Protocol)."""
from typing import Protocol
from uuid import UUID

from backend.src.domain.departments.entities import Department


class IDepartmentRepository(Protocol):
    async def add(self, department: Department) -> Department:
        """Persist a new department."""
        ...

    async def get_by_id(self, department_id: UUID) -> Department | None:
        """Load department by primary key."""
        ...

    async def save(self, department: Department) -> Department:
        """Insert or update a department."""
        ...
