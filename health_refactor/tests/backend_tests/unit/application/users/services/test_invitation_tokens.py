"""Unit tests: application/users/services/invitation_tokens.py"""
import re

from backend.src.application.users.services.invitation_tokens import (
    build_invitation_link,
    generate_invitation_token,
)


def test_generate_invitation_token_is_url_safe_and_long() -> None:
    token = generate_invitation_token()
    assert len(token) >= 32
    assert re.fullmatch(r"[\w\-]+", token)


def test_build_invitation_link_uses_product_base_url(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.src.application.users.services.invitation_tokens.settings.product_app_base_url",
        "http://localhost:3000/",
    )
    link = build_invitation_link(
        department_name="Acme Corp",
        user_email="jane@acme.com",
        token="abc123",
    )
    assert (
        link
        == "http://localhost:3000/invite?dept=Acme+Corp"
        "&user_email=jane%40acme.com&su_o=true&token=abc123"
    )


def test_build_invitation_link_url_encodes_special_characters(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.src.application.users.services.invitation_tokens.settings.product_app_base_url",
        "https://frontend-domain.com",
    )
    link = build_invitation_link(
        department_name="Acme & Co",
        user_email="jane+tag@acme.com",
        token="tok/en",
    )

    assert link.startswith("https://frontend-domain.com/invite?")
    assert "dept=Acme+%26+Co" in link
    assert "user_email=jane%2Btag%40acme.com" in link
    assert "su_o=true" in link
    assert "token=tok%2Fen" in link
