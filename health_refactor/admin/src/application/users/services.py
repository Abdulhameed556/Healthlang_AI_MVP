"""Application services for users."""
import secrets
from urllib.parse import urlencode

from admin.src.core.config import settings


def generate_invitation_token() -> str:
    return secrets.token_urlsafe(32)


def build_invitation_link(*, token: str) -> str:
    base = settings.admin_app_base_url.rstrip("/")
    query = urlencode({"token": token})
    return f"{base}/invite?{query}"
