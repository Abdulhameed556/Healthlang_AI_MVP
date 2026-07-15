"""
Pydantic request/response schemas for admin authentication.

Login is a two-step flow:
  1. ``/login/initiate`` — email + password, triggers an OTP email.
  2. ``/login/verify``   — email + OTP, returns the access token.

``EmailStr`` is intentionally avoided (the ``email-validator`` package is not a
dependency); emails are normalised with a small validator instead.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


def _normalise_email(value: str) -> str:
    value = value.strip().lower()
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise ValueError("Invalid email address")
    return value


class LoginInitiateRequest(BaseModel):
    """Step 1 of admin login — submit credentials to receive an email OTP."""

    email: str = Field(
        description="Admin account email (case-insensitive).",
        examples=["admin@platform.com"],
    )
    password: str = Field(
        min_length=1,
        description="Admin account password.",
        examples=["S3cure-Pass!"],
    )

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return _normalise_email(value)


class LoginInitiateResponse(BaseModel):
    """Confirms an OTP has been dispatched to the admin's email."""

    message: str = Field(
        description="Human-readable confirmation.",
        examples=["OTP sent to your email"],
    )

    model_config = {
        "json_schema_extra": {"example": {"message": "OTP sent to your email"}}
    }


class LoginVerifyRequest(BaseModel):
    """Step 2 of admin login — submit the 6-digit OTP to get an access token."""

    email: str = Field(
        description="Same email used in step 1.",
        examples=["admin@platform.com"],
    )
    otp: str = Field(
        min_length=6,
        max_length=6,
        description="6-digit one-time code from the login email.",
        examples=["482913"],
    )

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return _normalise_email(value)


class LoginVerifyResponse(BaseModel):
    """Issued access token (60-minute session, no refresh token)."""

    access_token: str = Field(
        description="Admin JWT. Send as `Authorization: Bearer <token>`.",
        examples=["eyJhbGciOiJIUzI1NiIs..."],
    )
    token_type: str = Field(
        default="bearer", description="Always `bearer`.", examples=["bearer"]
    )
    must_change_password: bool = Field(
        default=False,
        description="True if the admin should change their password (advisory; not enforced).",
        examples=[False],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "bearer",
                "must_change_password": False,
            }
        }
    }


class LogoutResponse(BaseModel):
    """Confirms the current admin session was invalidated."""

    message: str = Field(
        description="Human-readable confirmation.",
        examples=["Logged out"],
    )

    model_config = {"json_schema_extra": {"example": {"message": "Logged out"}}}
