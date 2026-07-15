"""Results for requesting break-glass access."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class RequestBreakGlassAccessResult:
    request_id: UUID
    target_patient_id: UUID
    needs_review: bool
    created_at: datetime
