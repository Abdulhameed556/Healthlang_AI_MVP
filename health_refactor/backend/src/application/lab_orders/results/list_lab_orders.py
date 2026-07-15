"""Results for listing an encounter's lab orders."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class LabOrderSummary:
    lab_order_id: UUID
    test_type: str
    status: str
    result_payload: str | None
    created_at: datetime
    fulfilled_at: datetime | None


@dataclass(frozen=True)
class ListLabOrdersResult:
    orders: list[LabOrderSummary]
