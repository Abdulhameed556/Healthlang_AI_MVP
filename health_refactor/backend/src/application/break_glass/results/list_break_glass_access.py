"""Results for listing break-glass access requests needing review."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class BreakGlassAccessSummary:
    request_id: UUID
    requesting_user_id: UUID
    target_patient_id: UUID
    reason: str
    created_at: datetime


@dataclass(frozen=True)
class ListBreakGlassAccessResult:
    requests: list[BreakGlassAccessSummary]
