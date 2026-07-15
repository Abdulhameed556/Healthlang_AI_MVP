"""Commands for requesting break-glass access."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RequestBreakGlassAccessCommand:
    requesting_user_id: UUID
    requesting_user_role: str
    target_patient_id: UUID
    reason: str
    ip_address: str | None = None
