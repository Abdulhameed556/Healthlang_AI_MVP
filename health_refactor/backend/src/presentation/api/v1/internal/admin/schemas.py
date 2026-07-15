"""Request/response schemas for Admin Portal internal routes."""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CreateInvitedUserFromAdminRequest(BaseModel):
    email: EmailStr = Field(..., description="Super-admin login email (normalized to lowercase).")
    department_name: str = Field(
        ..., min_length=1, max_length=255, description="Display name of the new department."
    )
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(
        default=None, max_length=5000, description="Optional department description."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "admin@hospital.example",
                "department_name": "Emergency Department",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "description": "Handles trauma and acute care.",
            }
        }
    )


class CreateInvitedUserFromAdminResponse(BaseModel):
    department_id: UUID = Field(..., description="New department UUID.")
    user_id: UUID = Field(..., description="Invited super-admin user UUID.")
    invitation_id: UUID = Field(..., description="Pending invitation UUID.")
    invitation_link: str = Field(
        ...,
        description="Full invite URL sent to the invitee (token is embedded; not returned separately).",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "department_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "550e8400-e29b-41d4-a716-446655440001",
                "invitation_id": "550e8400-e29b-41d4-a716-446655440002",
                "invitation_link": (
                    "https://app.example.com/invite?dept=Emergency+Department"
                    "&user_email=admin%40example.com&token=url-safe-token"
                ),
            }
        },
    )
