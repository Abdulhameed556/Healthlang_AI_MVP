"""Results for the department dashboard."""
from dataclasses import dataclass


@dataclass(frozen=True)
class GetDepartmentDashboardResult:
    total_patients_seen: int
    active_encounters: int
    discharged_encounters: int
    low_stock_items_count: int
    average_visit_duration_minutes: float | None
    esi_distribution: dict[int, int]
