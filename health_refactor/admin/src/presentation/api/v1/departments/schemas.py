"""Pydantic request/response schemas for departments."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _normalise_email(value: str) -> str:
    value = value.strip().lower()
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise ValueError("Invalid email address")
    return value


class InviteProductUserRequest(BaseModel):
    """Provision a new hospital department and invite its super-admin."""

    email: str = Field(
        description="Email of the department's super-admin (invitee).",
        examples=["ada.lovelace@hospital.example"],
    )
    department_name: str = Field(
        min_length=1, max_length=255,
        description="Display name of the new department.",
        examples=["Emergency Department"],
    )
    first_name: str = Field(
        min_length=1, max_length=100,
        description="Invitee's first name.",
        examples=["Ada"],
    )
    last_name: str = Field(
        min_length=1, max_length=100,
        description="Invitee's last name.",
        examples=["Lovelace"],
    )
    description: str | None = Field(
        default=None, max_length=5000,
        description="Optional department description.",
        examples=["Handles trauma and acute care"],
    )

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return _normalise_email(value)


class InviteProductUserResponse(BaseModel):
    """Result of provisioning the department + invitation."""

    status: str = Field(
        description="Always `success` on a 201.",
        examples=["success"],
    )
    email: str = Field(
        description="Invited email.",
        examples=["ada.lovelace@hospital.example"],
    )
    invitation_link: str = Field(
        description=(
            "Link the invitee opens to set their password and activate."
        ),
        examples=["http://localhost:3000/invite?token=xzx2gtB4Vn0f8c36"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "email": "ada.lovelace@hospital.example",
                "invitation_link": "http://localhost:3000/invite?token=abc",
            }
        }
    }


# ── List departments ───────────────────────────────────────────────────────


class DepartmentListItem(BaseModel):
    """Summary of a department for the list endpoint."""

    id: UUID = Field(description="Department unique ID.")
    name: str = Field(description="Department display name.")
    status: str = Field(
        description="Activation status: active, pending, or disabled.",
    )
    created_at: datetime = Field(
        description="Timestamp when the department was created.",
    )


class DepartmentListResponse(BaseModel):
    """Response for GET /departments."""

    departments: list[DepartmentListItem]
    total: int = Field(description="Total number of departments.")


# ── Department detail ──────────────────────────────────────────────────────


class DepartmentUserItem(BaseModel):
    """A user entry in a department detail response."""

    email: str
    first_name: str
    last_name: str
    role: str = Field(
        description=(
            "Hospital staff role: super_admin, admin, doctor, nurse, "
            "lab_scientist, pharmacist, or front_desk."
        ),
    )


class DepartmentDetailResponse(BaseModel):
    """Full department detail with user list."""

    id: UUID
    name: str
    description: str | None = None
    status: str
    created_at: datetime
    users: list[DepartmentUserItem]
