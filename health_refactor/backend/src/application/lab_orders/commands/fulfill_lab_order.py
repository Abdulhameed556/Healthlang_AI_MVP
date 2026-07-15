"""Commands for fulfilling a lab order."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class FulfillLabOrderCommand:
    lab_order_id: UUID
    fulfilled_by: UUID
    result_payload: str
