"""Token and link helpers for password reset flows."""
import secrets
from urllib.parse import urlencode

from backend.src.core.config import settings


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(32)


def build_password_reset_link(email: str, token: str) -> str:
    base = settings.product_app_base_url.rstrip("/")
    query = urlencode({"email": email, "token": token})
    return f"{base}/auth/reset-password?{query}"
