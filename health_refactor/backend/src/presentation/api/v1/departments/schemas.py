"""Pydantic request/response schemas for departments."""
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from backend.src.domain.departments.value_objects import DepartmentStatus
from backend.src.domain.users.value_objects import UserRole, UserStatus


class UpdateDepartmentProfileRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Department display name.",
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Optional department description; send empty string to clear.",
    )

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "UpdateDepartmentProfileRequest":
        if self.name is None and self.description is None:
            raise ValueError("At least one of name or description is required")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Emergency Department",
                "description": "Updated description",
            }
        }
    )


class DepartmentProfileResponse(BaseModel):
    department_id: UUID
    name: str
    description: str | None = None
    status: DepartmentStatus

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "department_id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Emergency Department",
                "description": "Handles trauma and acute care.",
                "status": "active",
            }
        },
    )


class DepartmentMemberResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus

    model_config = ConfigDict(from_attributes=True)


class ListDepartmentUsersResponse(BaseModel):
    users: list[DepartmentMemberResponse]
    total: int = Field(description="Total active and invited members in the department.")
    page: int = Field(description="Current page number (1-based).")
    page_size: int = Field(description="Number of members per page.")
    total_pages: int = Field(description="Total number of pages.")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "users": [
                    {
                        "user_id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "admin@hospital.example",
                        "first_name": "Ada",
                        "last_name": "Lovelace",
                        "role": "super_admin",
                        "status": "active",
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "total_pages": 1,
            }
        },
    )


class InvitableRole(StrEnum):
    """Roles assignable when inviting a teammate (not super_admin or admin)."""

    DOCTOR = "doctor"
    NURSE = "nurse"
    LAB_SCIENTIST = "lab_scientist"
    PHARMACIST = "pharmacist"
    FRONT_DESK = "front_desk"


class AssignableMemberRole(StrEnum):
    """Roles an admin may assign when changing a member's role."""

    DOCTOR = "doctor"
    NURSE = "nurse"
    LAB_SCIENTIST = "lab_scientist"
    PHARMACIST = "pharmacist"
    FRONT_DESK = "front_desk"


class SuperAdminAssignableMemberRole(StrEnum):
    """Roles a super_admin may assign when changing a member's role."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    DOCTOR = "doctor"
    NURSE = "nurse"
    LAB_SCIENTIST = "lab_scientist"
    PHARMACIST = "pharmacist"
    FRONT_DESK = "front_desk"


class UpdateDepartmentMemberRoleRequest(BaseModel):
    role: AssignableMemberRole | SuperAdminAssignableMemberRole = Field(
        ...,
        description="New department role for the member.",
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"role": "nurse"}}
    )


class UpdateDepartmentMemberRoleResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus

    model_config = ConfigDict(from_attributes=True)


class RemoveDepartmentMemberResponse(BaseModel):
    user_id: UUID = Field(..., description="Removed member UUID.")

    model_config = ConfigDict(from_attributes=True)


class InviteUserRequest(BaseModel):
    email: EmailStr = Field(..., description="Invitee email (normalized to lowercase).")
    role: InvitableRole = Field(..., description="Department role for the invitee.")
    first_name: str | None = Field(
        default=None,
        max_length=100,
        description="Optional; placeholder used until invitee accepts.",
    )
    last_name: str | None = Field(
        default=None,
        max_length=100,
        description="Optional; placeholder used until invitee accepts.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "teammate@hospital.example",
                "role": "nurse",
                "first_name": "Ada",
                "last_name": "Lovelace",
            }
        }
    )


class InviteUserResponse(BaseModel):
    user_id: UUID = Field(..., description="Invited user UUID.")
    invitation_id: UUID = Field(..., description="Pending invitation UUID.")
    email: EmailStr = Field(..., description="Normalized invitee email.")
    role: InvitableRole = Field(..., description="Role assigned on the invitation.")
    invitation_link: str = Field(
        ...,
        description="Full invite URL (token embedded; useful in development).",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "invitation_id": "550e8400-e29b-41d4-a716-446655440001",
                "email": "teammate@hospital.example",
                "role": "nurse",
                "invitation_link": (
                    "http://localhost:3000/invite?dept=Emergency+Department"
                    "&user_email=invite%40example.com&token=url-safe-token"
                ),
            }
        },
    )
