"""OpenAPI paths that do not require a Bearer JWT (documentation only)."""
import re

PUBLIC_BACKEND_PATHS = frozenset(
    {
        "/api/v1/health",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/google/url",
        "/api/v1/auth/google",
        "/api/v1/auth/password-reset/request",
        "/api/v1/auth/password-reset/complete",
    }
)
PUBLIC_BACKEND_PATH_PATTERNS = (
    re.compile(r"^/api/v1/invitations/[^/]+/decline$"),
)
PUBLIC_ADMIN_PATHS = frozenset(
    {
        "/admin/api/v1/health",
        "/admin/api/v1/auth/login/initiate",
        "/admin/api/v1/auth/login/verify",
    }
)


def is_public_backend_path(path: str) -> bool:
    if path in PUBLIC_BACKEND_PATHS:
        return True
    return any(pattern.match(path) for pattern in PUBLIC_BACKEND_PATH_PATTERNS)


def is_public_openapi_path(path: str) -> bool:
    if path in PUBLIC_ADMIN_PATHS:
        return True
    return is_public_backend_path(path)
