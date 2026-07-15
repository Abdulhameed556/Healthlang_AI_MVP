"""Commands for reviewing a break-glass access request."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ReviewBreakGlassAccessCommand:
    request_id: UUID
    reviewed_by: UUID
