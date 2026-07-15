"""Results for fulfilling a lab order."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class FulfillLabOrderResult:
    lab_order_id: UUID
    status: str
    result_payload: str
    fulfilled_at: datetime
