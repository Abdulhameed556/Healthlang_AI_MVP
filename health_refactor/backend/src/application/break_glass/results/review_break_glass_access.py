"""Results for reviewing a break-glass access request."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ReviewBreakGlassAccessResult:
    request_id: UUID
    needs_review: bool
    reviewed_by: UUID
    reviewed_at: datetime
