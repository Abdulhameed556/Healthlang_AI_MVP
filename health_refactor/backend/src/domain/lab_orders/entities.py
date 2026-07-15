"""Domain entities for lab orders."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class LabOrder:
    id: UUID
    encounter_id: UUID
    ordered_by: UUID
    test_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    result_payload: str | None = None
    fulfilled_by: UUID | None = None
    fulfilled_at: datetime | None = None
