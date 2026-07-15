"""Use-case: load the caller's department dashboard stats."""
from backend.src.application.dashboard.commands.get_department_dashboard import (
    GetDepartmentDashboardCommand,
)
from backend.src.application.dashboard.results.get_department_dashboard import (
    GetDepartmentDashboardResult,
)
from backend.src.domain.dashboard.repositories import IDashboardRepository


class GetDepartmentDashboard:
    def __init__(self, dashboard_repository: IDashboardRepository) -> None:
        self._dashboard_repository = dashboard_repository

    async def execute(
        self, command: GetDepartmentDashboardCommand
    ) -> GetDepartmentDashboardResult:
        stats = await self._dashboard_repository.get_department_stats(
            command.department_id
        )
        return GetDepartmentDashboardResult(
            total_patients_seen=stats.total_patients_seen,
            active_encounters=stats.active_encounters,
            discharged_encounters=stats.discharged_encounters,
            low_stock_items_count=stats.low_stock_items_count,
            average_visit_duration_minutes=stats.average_visit_duration_minutes,
            esi_distribution=stats.esi_distribution,
        )
