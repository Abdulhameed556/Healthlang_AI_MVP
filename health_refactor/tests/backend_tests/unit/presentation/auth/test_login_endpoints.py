"""Unit tests: auth login endpoint schemas and basic flow."""
import pytest
from pydantic import ValidationError

from backend.src.presentation.api.v1.auth.schemas import LoginRequest


class TestLoginSchemas:
    def test_email_normalised(self):
        req = LoginRequest(email="  User@Example.COM ", password="password123", is_new=False)
        assert req.email == "user@example.com"

    def test_invalid_email_rejected(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="not-an-email", password="password123", is_new=False)
