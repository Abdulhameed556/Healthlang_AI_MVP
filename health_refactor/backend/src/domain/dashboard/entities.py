"""Read-model for the department dashboard — not a persisted entity, just the
shape of the aggregate stats query."""
from dataclasses import dataclass, field


@dataclass
class DepartmentDashboardStats:
    total_patients_seen: int
    active_encounters: int
    discharged_encounters: int
    low_stock_items_count: int
    average_visit_duration_minutes: float | None = None
    esi_distribution: dict[int, int] = field(default_factory=dict)
