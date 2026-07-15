"""Pydantic response schemas for the audit log."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogEntryResponse(BaseModel):
    log_id: UUID
    actor_id: UUID | None = None
    actor_role: str | None = None
    department_id: UUID | None = None
    action: str
    target_entity_id: str | None = None
    ip_address: str | None = None
    outcome: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListAuditLogResponse(BaseModel):
    logs: list[AuditLogEntryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)
