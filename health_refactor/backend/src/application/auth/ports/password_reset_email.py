"""Email delivery port for password reset flows."""
from typing import Protocol


class IPasswordResetEmailSender(Protocol):
    async def send_password_reset(
        self,
        *,
        to_email: str,
        reset_link: str,
    ) -> None:
        """Deliver password reset email to the user."""
        ...
