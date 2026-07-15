"""Admin Portal → Backend authentication (shared API key, server-to-server)."""
import secrets

from fastapi import Header, HTTPException, Security
from fastapi.security import APIKeyHeader

from backend.src.core.config import settings

ADMIN_API_KEY_HEADER = "X-Admin-Api-Key"

admin_api_key_header = APIKeyHeader(
    name=ADMIN_API_KEY_HEADER,
    auto_error=False,
    description="Admin Portal internal API key (server-to-server). Not product user JWT.",
)


def _extract_admin_api_key(
    x_admin_api_key: str | None,
    authorization: str | None,
) -> str | None:
    if x_admin_api_key:
        return x_admin_api_key.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


async def require_admin_api_key(
    x_admin_api_key: str | None = Security(admin_api_key_header),
    authorization: str | None = Header(default=None, include_in_schema=False),
) -> None:
    """Reject requests without a valid Admin Portal internal API key."""
    provided = _extract_admin_api_key(x_admin_api_key, authorization)
    expected = settings.admin_internal_api_key

    if not expected or not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing admin API key")
