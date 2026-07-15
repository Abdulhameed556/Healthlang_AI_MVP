"""Write an audit log entry with its own DB session.

Used from the audit-logging middleware, which runs outside FastAPI's normal
per-request dependency-injection lifecycle and so cannot receive a session
via `Depends(get_db)`.
"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from backend.src.domain.audit.entities import AuditLog
from backend.src.infrastructure.database.session import async_session_factory
from backend.src.infrastructure.repositories.audit_logs import SqlAlchemyAuditLogRepository


async def write_audit_log(
    *,
    action: str,
    outcome: str,
    actor_id: UUID | None = None,
    actor_role: str | None = None,
    department_id: UUID | None = None,
    target_entity_id: str | None = None,
    ip_address: str | None = None,
) -> None:
    async with async_session_factory() as session:
        repository = SqlAlchemyAuditLogRepository(session)
        await repository.add(
            AuditLog(
                id=uuid4(),
                actor_id=actor_id,
                actor_role=actor_role,
                department_id=department_id,
                action=action,
                target_entity_id=target_entity_id,
                ip_address=ip_address,
                outcome=outcome,
                created_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()
