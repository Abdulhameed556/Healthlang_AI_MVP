"""Domain entities for break-glass (emergency) access.

A scoped, time-boxed read exception rather than a permanent permission
change — the requesting clinician states a reason, and the event is
auto-flagged for a super_admin to review afterward.
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class BreakGlassAccess:
    id: UUID
    requesting_user_id: UUID
    target_patient_id: UUID
    reason: str
    needs_review: bool
    created_at: datetime
    reviewed_by: UUID | None = None
    reviewed_at: datetime | None = None
