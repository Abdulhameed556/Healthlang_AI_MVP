"""Token and link helpers for invitation flows."""
import secrets
from urllib.parse import urlencode

from backend.src.core.config import settings


def generate_invitation_token() -> str:
    return secrets.token_urlsafe(32)


def build_invitation_link(
    *,
    department_name: str,
    user_email: str,
    token: str,
) -> str:
    base = settings.product_app_base_url.rstrip("/")
    query = urlencode(
        {
            "dept": department_name,
            "user_email": user_email,
            "su_o": "true",
            "token": token,
        }
    )
    return f"{base}/invite?{query}"
