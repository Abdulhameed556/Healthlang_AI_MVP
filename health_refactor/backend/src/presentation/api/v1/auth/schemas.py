"""Pydantic request/response schemas for auth."""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from backend.src.domain.users.value_objects import UserRole


class LoginRequest(BaseModel):
    """Login for existing users or invitation activation (``is_new=true``)."""

    password: str = Field(..., min_length=8, description="Account password.")
    is_new: bool = Field(
        False,
        description="True when accepting an invitation from the invite link.",
    )
    email: EmailStr | None = Field(
        None,
        description="Required for normal login; optional for invite login (resolved from token).",
    )
    invitation_token: str | None = Field(
        None,
        description="Invitation token from the invite link; required when ``is_new`` is true.",
    )

    @model_validator(mode="after")
    def validate_login_mode(self) -> "LoginRequest":
        if self.email:
            self.email = self.email.strip().lower()  # type: ignore[assignment]
        if self.is_new:
            if not self.invitation_token:
                raise ValueError("invitation_token is required when is_new is true")
        elif not self.email:
            raise ValueError("email is required when is_new is false")
        return self


class LoginDepartmentResponse(BaseModel):
    department_id: UUID
    department_name: str

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: UUID
    email: EmailStr
    role: UserRole
    departments: list[LoginDepartmentResponse] = Field(
        ...,
        description="Active departments for this email (id and name).",
    )
    activated_invitation: bool = Field(
        ...,
        description="True when this login completed invitation acceptance.",
    )

    model_config = ConfigDict(from_attributes=True)


class GoogleOAuthUrlResponse(BaseModel):
    oauth_url: str = Field(..., description="Google OAuth authorization URL for the SPA.")


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Account email address.")

    @model_validator(mode="after")
    def normalize_email(self) -> "RequestPasswordResetRequest":
        self.email = self.email.strip().lower()  # type: ignore[assignment]
        return self


class CompletePasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Email from the reset link.")
    token: str = Field(..., min_length=1, description="Reset token from the link.")
    new_password: str = Field(..., min_length=8, description="New account password.")

    @model_validator(mode="after")
    def normalize_email(self) -> "CompletePasswordResetRequest":
        self.email = self.email.strip().lower()  # type: ignore[assignment]
        self.token = self.token.strip()
        return self


class RequestPasswordResetResponse(BaseModel):
    message: str
    reset_link: str | None = Field(
        default=None,
        description=(
            "Reset URL for local testing when outbound email is disabled. "
            "Omitted in production after the email is sent."
        ),
    )

    model_config = ConfigDict(from_attributes=True)


class PasswordResetMessageResponse(BaseModel):
    message: str

    model_config = ConfigDict(from_attributes=True)


class GoogleLoginRequest(BaseModel):
    """Google OAuth callback: exchange ``code`` for a session."""

    code: str = Field(..., min_length=1, description="Authorization code from Google.")
    is_new: bool = Field(
        False,
        description="True when accepting an invitation via Google.",
    )
    invitation_token: str | None = Field(
        None,
        description="Invitation token from the invite link; required when ``is_new`` is true.",
    )

    @model_validator(mode="after")
    def validate_google_login_mode(self) -> "GoogleLoginRequest":
        if self.is_new and not self.invitation_token:
            raise ValueError("invitation_token is required when is_new is true")
        return self
