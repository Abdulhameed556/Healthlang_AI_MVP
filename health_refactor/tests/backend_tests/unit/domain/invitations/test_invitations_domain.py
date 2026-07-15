"""Unit tests: domain/invitations."""
from datetime import datetime, timezone
from uuid import uuid4

from backend.src.core.exceptions import NotFoundError, ValidationError
from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.exceptions import (
    InvitationEmailMismatchError,
    InvitationExpiredError,
    InvitationNotFoundError,
    InvitationNotPendingError,
)
from backend.src.domain.invitations.value_objects import InvitationRole, InvitationStatus
from backend.src.domain.users.value_objects import UserRole


class TestInvitationValueObjects:
    def test_status_values(self) -> None:
        assert InvitationStatus.PENDING == "pending"
        assert InvitationStatus.DECLINED == "declined"
        assert InvitationRole is UserRole


class TestInvitationEntity:
    def test_construct_pending_invitation(self) -> None:
        invitation = Invitation(
            id=uuid4(),
            department_id=uuid4(),
            email="invite@example.com",
            role=UserRole.NURSE,
            token="secure-token",
            status=InvitationStatus.PENDING,
            expires_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        assert invitation.invited_by is None
        assert invitation.accepted_at is None


class TestInvitationExceptions:
    def test_hierarchy(self) -> None:
        assert issubclass(InvitationNotFoundError, NotFoundError)
        assert issubclass(InvitationExpiredError, ValidationError)
        assert issubclass(InvitationNotPendingError, ValidationError)
        assert issubclass(InvitationEmailMismatchError, ValidationError)
