"""Domain exceptions for invitations."""
from backend.src.core.exceptions import ConflictError, NotFoundError, ValidationError


class InvitationNotFoundError(NotFoundError):
    """Raised when invitation token or id is unknown."""


class InvitationExpiredError(ValidationError):
    """Raised when invitation token is past expires_at."""


class InvitationNotPendingError(ValidationError):
    """Raised when invitation is not in pending status."""


class InvitationEmailMismatchError(ValidationError):
    """Raised when accept flow email does not match invited email."""


class InvitationAlreadyExistsError(ConflictError):
    """Raised when a pending invite already exists for the email."""
