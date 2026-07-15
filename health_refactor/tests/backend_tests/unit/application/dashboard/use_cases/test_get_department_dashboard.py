"""Unit tests: application/dashboard/use_cases/get_department_dashboard.py"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.dashboard.commands.get_department_dashboard import (
    GetDepartmentDashboardCommand,
)
from backend.src.application.dashboard.use_cases.get_department_dashboard import (
    GetDepartmentDashboard,
)
from backend.src.domain.dashboard.entities import DepartmentDashboardStats


@pytest.mark.asyncio
async def test_execute_returns_mapped_stats() -> None:
    repo = AsyncMock()
    stats = DepartmentDashboardStats(
        total_patients_seen=142,
        active_encounters=6,
        discharged_encounters=136,
        low_stock_items_count=2,
        average_visit_duration_minutes=47.5,
        esi_distribution={1: 1, 2: 8, 3: 40, 4: 70, 5: 17},
    )
    repo.get_department_stats = AsyncMock(return_value=stats)
    use_case = GetDepartmentDashboard(dashboard_repository=repo)
    dept_id = uuid4()

    result = await use_case.execute(GetDepartmentDashboardCommand(department_id=dept_id))

    repo.get_department_stats.assert_awaited_once_with(dept_id)
    assert result.total_patients_seen == 142
    assert result.esi_distribution == {1: 1, 2: 8, 3: 40, 4: 70, 5: 17}
    assert result.average_visit_duration_minutes == 47.5
