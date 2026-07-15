"""Unit tests: ORM ↔ domain mappers."""
from datetime import datetime, timezone
from uuid import uuid4

from backend.src.domain.invitations.entities import Invitation
from backend.src.domain.invitations.value_objects import InvitationStatus
from backend.src.domain.departments.entities import Department
from backend.src.domain.departments.value_objects import DepartmentStatus
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus
from backend.src.infrastructure.repositories._mappers import (
    invitation_to_entity,
    invitation_to_model,
    department_to_entity,
    department_to_model,
    user_to_entity,
    user_to_model,
)


class TestDepartmentMapper:
    def test_round_trip(self) -> None:
        entity = Department(
            id=uuid4(),
            name="Emergency Department",
            description="Trauma and acute care",
            status=DepartmentStatus.INVITED,
            created_at=datetime.now(timezone.utc),
        )
        restored = department_to_entity(department_to_model(entity))
        assert restored == entity


class TestUserMapper:
    def test_round_trip_invited_user(self) -> None:
        now = datetime.now(timezone.utc)
        entity = User(
            id=uuid4(),
            department_id=uuid4(),
            first_name="A",
            last_name="B",
            email="user@example.com",
            role=UserRole.ADMIN,
            status=UserStatus.INVITED,
            auth_method=UserAuthMethod.EMAIL_PASSWORD,
            created_at=now,
            updated_at=now,
        )
        restored = user_to_entity(user_to_model(entity))
        assert restored == entity


class TestInvitationMapper:
    def test_round_trip(self) -> None:
        now = datetime.now(timezone.utc)
        entity = Invitation(
            id=uuid4(),
            department_id=uuid4(),
            email="invite@example.com",
            role=UserRole.ADMIN,
            token="tok",
            status=InvitationStatus.PENDING,
            expires_at=now,
            created_at=now,
        )
        restored = invitation_to_entity(invitation_to_model(entity))
        assert restored == entity
