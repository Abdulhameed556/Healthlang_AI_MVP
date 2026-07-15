"""Unit tests: domain/users."""
from datetime import datetime, timezone
from uuid import uuid4

from backend.src.core.exceptions import ConflictError, NotFoundError
from backend.src.domain.users.entities import User
from backend.src.domain.users.exceptions import UserAlreadyExistsError, UserNotFoundError
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus


class TestUserValueObjects:
    def test_status_values_match_product_contract(self) -> None:
        assert UserStatus.INVITED == "invited"
        assert UserStatus.ACTIVE == "active"

    def test_role_values(self) -> None:
        assert UserRole.SUPER_ADMIN == "super_admin"
        assert UserRole.ADMIN == "admin"
        assert UserAuthMethod.EMAIL_PASSWORD == "email_password"


class TestUserEntity:
    def test_construct_invited_user_without_password(self) -> None:
        now = datetime.now(timezone.utc)
        dept_id = uuid4()
        user = User(
            id=uuid4(),
            department_id=dept_id,
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            role=UserRole.ADMIN,
            status=UserStatus.INVITED,
            auth_method=UserAuthMethod.EMAIL_PASSWORD,
            created_at=now,
            updated_at=now,
        )
        assert user.password_hash is None
        assert user.status == "invited"


class TestUserExceptions:
    def test_not_found_is_not_found_error(self) -> None:
        assert issubclass(UserNotFoundError, NotFoundError)

    def test_already_exists_is_conflict_error(self) -> None:
        assert issubclass(UserAlreadyExistsError, ConflictError)
