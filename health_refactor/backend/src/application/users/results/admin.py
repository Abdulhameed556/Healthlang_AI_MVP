"""Results for admin-driven user provisioning."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreateInvitedUserFromAdminResult:
    """Result returned to Admin Portal after provisioning."""

    department_id: UUID
    user_id: UUID
    invitation_id: UUID
    invitation_token: str
    invitation_link: str
