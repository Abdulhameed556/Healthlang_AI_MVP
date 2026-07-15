"""FastAPI dependency-injection providers for dashboard use-cases."""
from fastapi import Depends

from backend.src.application.dashboard.use_cases.get_department_dashboard import (
    GetDepartmentDashboard,
)
from backend.src.domain.dashboard.repositories import IDashboardRepository
from backend.src.infrastructure.database.dependencies import get_dashboard_repository


def get_get_department_dashboard(
    dashboard_repository: IDashboardRepository = Depends(get_dashboard_repository),
) -> GetDepartmentDashboard:
    return GetDepartmentDashboard(dashboard_repository=dashboard_repository)
