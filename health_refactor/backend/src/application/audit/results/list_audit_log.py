"""Results for listing the audit log."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AuditLogEntry:
    log_id: UUID
    actor_id: UUID | None
    actor_role: str | None
    department_id: UUID | None
    action: str
    target_entity_id: str | None
    ip_address: str | None
    outcome: str
    created_at: datetime


@dataclass(frozen=True)
class ListAuditLogResult:
    logs: list[AuditLogEntry]
    total: int
    page: int
    page_size: int
    total_pages: int
