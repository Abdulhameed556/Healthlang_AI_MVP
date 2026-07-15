"""Schema validation tests for auth."""
import pytest
from pydantic import ValidationError

from backend.src.presentation.api.v1.auth.schemas import (
    CompletePasswordResetRequest,
    GoogleLoginRequest,
    GoogleOAuthUrlResponse,
    LoginDepartmentResponse,
    LoginRequest,
    LoginResponse,
    PasswordResetMessageResponse,
    RequestPasswordResetRequest,
    RequestPasswordResetResponse,
)


def test_google_login_requires_invitation_token_when_is_new() -> None:
    with pytest.raises(ValidationError, match="invitation_token"):
        GoogleLoginRequest(code="abc", is_new=True)


def test_google_login_accepts_invite_mode() -> None:
    body = GoogleLoginRequest(
        code="google-code",
        is_new=True,
        invitation_token="invite-token",
    )
    assert body.invitation_token == "invite-token"


def test_login_requires_email_when_not_invite() -> None:
    with pytest.raises(ValidationError, match="email"):
        LoginRequest(password="longpassword", is_new=False)


def test_login_requires_invitation_token_when_is_new() -> None:
    with pytest.raises(ValidationError, match="invitation_token"):
        LoginRequest(password="longpassword", is_new=True)


def test_login_accepts_invite_mode_without_email() -> None:
    body = LoginRequest(
        password="longpassword",
        is_new=True,
        invitation_token="invite-token",
    )
    assert body.email is None
    assert body.invitation_token == "invite-token"


def test_request_password_reset_normalizes_email() -> None:
    body = RequestPasswordResetRequest(email="User@Example.com")

    assert body.email == "user@example.com"


def test_request_password_reset_response_accepts_optional_reset_link() -> None:
    response = RequestPasswordResetResponse(
        message="If an account exists for this email, a password reset link has been sent.",
        reset_link="http://localhost:3000/auth/reset-password?email=u%40e.com&token=tok",
    )

    assert response.reset_link is not None


def test_complete_password_reset_normalizes_email_and_token() -> None:
    body = CompletePasswordResetRequest(
        email=" User@Example.com ",
        token="  reset-token  ",
        new_password="new-secret",
    )

    assert body.email == "user@example.com"
    assert body.token == "reset-token"


def test_complete_password_reset_requires_minimum_password_length() -> None:
    with pytest.raises(ValidationError, match="new_password"):
        CompletePasswordResetRequest(
            email="user@example.com",
            token="reset-token",
            new_password="short",
        )


def test_password_reset_message_response_model() -> None:
    response = PasswordResetMessageResponse(message="Password reset successfully")

    assert response.message == "Password reset successfully"


def test_login_response_has_departments_not_top_level_department_id() -> None:
    assert "departments" in LoginResponse.model_fields
    assert "department_id" not in LoginResponse.model_fields


def test_login_response_and_google_url_response_models() -> None:
    from uuid import uuid4

    dept_id = uuid4()
    login = LoginResponse(
        access_token="token",
        refresh_token="refresh",
        user_id=uuid4(),
        email="user@example.com",
        role="nurse",
        departments=[
            LoginDepartmentResponse(
                department_id=dept_id,
                department_name="Acme Corp",
            )
        ],
        activated_invitation=True,
    )
    assert login.activated_invitation is True
    assert login.departments[0].department_name == "Acme Corp"

    url = GoogleOAuthUrlResponse(oauth_url="https://accounts.google.com/")
    assert "google" in url.oauth_url
