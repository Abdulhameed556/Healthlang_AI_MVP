"""Pydantic request/response schemas for admin user routes."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from admin.src.domain.users.entities import AdminRole, AdminUserStatus


class CurrentAdminResponse(BaseModel):
    """The authenticated admin's own profile.

    Admin users are not tied to a department, so there is no ``department_id``.
    The password hash and other sensitive fields are never returned.
    """

    user_id: UUID = Field(
        description="The admin's UUID.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    email: str = Field(description="Login email.", examples=["admin@platform.com"])
    first_name: str = Field(description="Given name.", examples=["Ada"])
    last_name: str = Field(description="Family name.", examples=["Min"])
    role: AdminRole = Field(
        description="`super_admin` or `read_only`.", examples=["super_admin"]
    )
    status: AdminUserStatus = Field(
        description="`pending`, `active`, or `locked`.", examples=["active"]
    )
    must_change_password: bool = Field(
        description="True if the admin should change their password (advisory; not enforced).",
        examples=[False],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "admin@platform.com",
                "first_name": "Ada",
                "last_name": "Min",
                "role": "super_admin",
                "status": "active",
                "must_change_password": False,
            }
        }
    }


# ── List / detail ────────────────────────────────────────────────────────


class AdminUserSummaryResponse(BaseModel):
    """One row in the admin-users list."""

    id: UUID
    email: str
    first_name: str
    last_name: str
    role: AdminRole
    status: AdminUserStatus
    created_at: datetime


class AdminUserListResponse(BaseModel):
    users: list[AdminUserSummaryResponse]
    total: int = Field(description="Total number of admin users.")


class AdminUserDetailResponse(BaseModel):
    """Full profile for one admin user. Password hash is never returned."""

    id: UUID
    email: str
    first_name: str
    last_name: str
    role: AdminRole
    status: AdminUserStatus
    google_linked: bool
    must_change_password: bool
    failed_attempts: int
    invited_by: UUID | None = None
    created_at: datetime
    updated_at: datetime


# ── Invite / resend ─────────────────────────────────────────────────────


class InviteAdminUserRequest(BaseModel):
    email: EmailStr = Field(description="Invitee email.", examples=["ada@platform.com"])
    first_name: str = Field(min_length=1, max_length=100, examples=["Ada"])
    last_name: str = Field(min_length=1, max_length=100, examples=["Min"])
    role: AdminRole = Field(
        description="`super_admin` or `read_only`.", examples=["read_only"]
    )

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class InviteAdminUserResponse(BaseModel):
    user_id: UUID
    invitation_id: UUID
    email: str
    role: AdminRole
    invitation_link: str = Field(
        description="Full invite URL (token embedded; useful in development)."
    )


# ── Edit role ────────────────────────────────────────────────────────────


class EditAdminUserRoleRequest(BaseModel):
    role: AdminRole = Field(description="New role for this admin user.")


# ── Accept invitation (public, token-gated) ─────────────────────────────


class AcceptInvitationRequest(BaseModel):
    token: str = Field(description="Invitation token from the invite link.")
    password: str = Field(min_length=8, description="New password to set.")


class AcceptInvitationResponse(BaseModel):
    status: str = Field(description="Always `success`.", examples=["success"])
    email: str = Field(description="The now-active admin's email.")
