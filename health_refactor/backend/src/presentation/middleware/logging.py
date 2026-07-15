"""Audit-logging middleware — the HIPAA-shaped access log for every request.

Runs outside FastAPI's per-request dependency injection, so it decodes the
bearer token itself (same JWT `decode_token` helper `require_auth` uses) and
opens its own DB session to resolve the actor's role/department and to write
the resulting AuditLog row. This covers every read and write generically;
`RequestBreakGlassAccess` additionally writes its own AuditLog row in the same
transaction as the domain change, since that one action is too
audit-sensitive to rely on a best-effort, after-the-fact log entry.
"""
import re
from uuid import UUID

from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from backend.src.application.audit.services.audit_writer import write_audit_log
from backend.src.core.security import decode_token
from backend.src.domain.audit.value_objects import AuditOutcome
from backend.src.infrastructure.database.session import async_session_factory
from backend.src.infrastructure.repositories.users import SqlAlchemyUserRepository

_EXCLUDED_PATH_PREFIXES = ("/api/v1/health", "/docs", "/redoc", "/openapi.json")
_UUID_PATTERN = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        path = request.url.path
        if any(path.startswith(prefix) for prefix in _EXCLUDED_PATH_PREFIXES):
            return response

        actor_id, actor_role, department_id = await self._resolve_actor(request)
        if actor_id is None:
            return response

        target_match = _UUID_PATTERN.search(path)
        outcome = (
            AuditOutcome.SUCCESS if response.status_code < 400 else AuditOutcome.FAILURE
        )

        await write_audit_log(
            actor_id=actor_id,
            actor_role=actor_role,
            department_id=department_id,
            action=f"{request.method} {path}",
            target_entity_id=target_match.group(0) if target_match else None,
            ip_address=request.client.host if request.client else None,
            outcome=outcome.value,
        )
        return response

    @staticmethod
    async def _resolve_actor(
        request: Request,
    ) -> tuple[UUID | None, str | None, UUID | None]:
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.lower().startswith("bearer "):
            return None, None, None

        token = authorization.split(" ", 1)[1].strip()
        try:
            payload = decode_token(token)
        except JWTError:
            return None, None, None

        user_id = payload.get("sub")
        if not user_id:
            return None, None, None

        async with async_session_factory() as session:
            user = await SqlAlchemyUserRepository(session).get_by_id(UUID(user_id))
            if user is None:
                return None, None, None
            return user.id, user.role, user.department_id
