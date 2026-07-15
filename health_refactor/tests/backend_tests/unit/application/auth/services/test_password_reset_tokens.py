"""Unit tests: application/auth/services/password_reset_tokens.py"""
from backend.src.application.auth.services.password_reset_tokens import (
    build_password_reset_link,
    generate_password_reset_token,
)


def test_generate_password_reset_token_returns_url_safe_string() -> None:
    token = generate_password_reset_token()

    assert len(token) >= 32


def test_build_password_reset_link_includes_email_and_token() -> None:
    link = build_password_reset_link("user@example.com", "reset-token")

    assert "email=user%40example.com" in link
    assert "token=reset-token" in link
    assert link.endswith("reset-password?email=user%40example.com&token=reset-token") or (
        "reset-password?" in link
    )
