"""Abstract repository interface for the department dashboard read-model."""
from typing import Protocol
from uuid import UUID

from backend.src.domain.dashboard.entities import DepartmentDashboardStats


class IDashboardRepository(Protocol):
    async def get_department_stats(
        self, department_id: UUID
    ) -> DepartmentDashboardStats: ...
