"""Department tenant context for multi-org product users."""
from uuid import UUID

from backend.src.core.exceptions import ForbiddenError

DEPARTMENT_ID_HEADER = "X-Department-Id"


def parse_department_id_header(value: str | None) -> UUID | None:
    """Parse optional ``X-Department-Id`` header value."""
    if value is None or not value.strip():
        return None
    try:
        return UUID(value.strip())
    except ValueError as exc:
        raise ForbiddenError("Invalid department id header") from exc
