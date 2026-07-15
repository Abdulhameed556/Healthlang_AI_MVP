"""Pydantic schemas for public invitation endpoints."""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class DeclineInvitationResponse(BaseModel):
    invitation_id: UUID
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)
