"""Pydantic response schemas for the department dashboard."""
from pydantic import BaseModel, ConfigDict


class DepartmentDashboardResponse(BaseModel):
    total_patients_seen: int
    active_encounters: int
    discharged_encounters: int
    low_stock_items_count: int
    average_visit_duration_minutes: float | None = None
    esi_distribution: dict[int, int]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "total_patients_seen": 142,
                "active_encounters": 6,
                "discharged_encounters": 136,
                "low_stock_items_count": 2,
                "average_visit_duration_minutes": 47.5,
                "esi_distribution": {"1": 1, "2": 8, "3": 40, "4": 70, "5": 17},
            }
        },
    )
