"""Commands for admin-driven user provisioning."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CreateInvitedUserFromAdminCommand:
    """Input from Admin Portal to provision a department + invited super-admin."""

    email: str
    department_name: str
    first_name: str
    last_name: str
    description: str | None = None
