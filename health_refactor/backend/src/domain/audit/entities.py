"""Domain entities for audit logging.

Five fields, matching the HIPAA-cited standard: who (actor_id + actor_role),
what (action + target_entity_id), when (created_at), from where (ip_address),
and outcome (success/failure). department_id scopes which department's audit
log this entry belongs to, for the Admin-sees-own-department-only read rule.
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class AuditLog:
    id: UUID
    action: str
    outcome: str
    created_at: datetime
    actor_id: UUID | None = None
    actor_role: str | None = None
    department_id: UUID | None = None
    target_entity_id: str | None = None
    ip_address: str | None = None
