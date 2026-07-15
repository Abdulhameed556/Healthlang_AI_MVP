"""Email delivery ports for user flows."""
from typing import Protocol


class IInvitationEmailSender(Protocol):
    async def send_invitation(
        self,
        *,
        to_email: str,
        invitation_link: str,
        department_name: str,
    ) -> None:
        """Deliver invitation email to the invited super-admin."""
        ...
