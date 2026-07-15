"""Unit tests: admin/src/presentation/api/v1/auth/schemas.py"""
import pytest
from pydantic import ValidationError

from admin.src.presentation.api.v1.auth.schemas import (
    LoginInitiateRequest,
    LoginVerifyRequest,
    _normalise_email,
)


def test_normalise_email_strips_and_lowercases() -> None:
    assert _normalise_email("  User@Example.COM  ") == "user@example.com"


def test_normalise_email_raises_for_missing_at() -> None:
    with pytest.raises(ValueError, match="Invalid email"):
        _normalise_email("notanemail")


def test_normalise_email_raises_for_leading_at() -> None:
    with pytest.raises(ValueError, match="Invalid email"):
        _normalise_email("@domain.com")


def test_normalise_email_raises_for_trailing_at() -> None:
    with pytest.raises(ValueError, match="Invalid email"):
        _normalise_email("user@")


def test_login_initiate_request_validates_email() -> None:
    req = LoginInitiateRequest(email="  ADMIN@Example.com  ", password="secret")
    assert req.email == "admin@example.com"


def test_login_initiate_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        LoginInitiateRequest(email="bad-email", password="secret")


def test_login_verify_request_validates_email() -> None:
    req = LoginVerifyRequest(email="Admin@Example.COM", otp="123456")
    assert req.email == "admin@example.com"


def test_login_verify_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        LoginVerifyRequest(email="@bad", otp="123456")
