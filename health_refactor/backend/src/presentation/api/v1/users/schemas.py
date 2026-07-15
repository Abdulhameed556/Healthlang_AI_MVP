"""Pydantic request/response schemas for users."""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


class UserDepartmentSummaryResponse(BaseModel):
    department_id: UUID
    department_name: str
    user_id: UUID
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class ListUserDepartmentsResponse(BaseModel):
    departments: list[UserDepartmentSummaryResponse]

    model_config = ConfigDict(from_attributes=True)


class CurrentUserProfileResponse(BaseModel):
    user_id: UUID
    department_id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus
    auth_method: UserAuthMethod

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "department_id": "550e8400-e29b-41d4-a716-446655440001",
                "email": "admin@acme.com",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "role": "admin",
                "status": "active",
                "auth_method": "email_password",
            }
        },
    )
