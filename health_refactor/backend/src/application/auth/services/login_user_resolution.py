"""Resolve which user row to authenticate when an email has multiple org memberships."""
from collections.abc import Callable, Sequence

from backend.src.core.exceptions import ForbiddenError
from backend.src.domain.auth.exceptions import InvalidCredentialsError
from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserStatus

_INVITATION_REQUIRED_MESSAGE = (
    "Complete your invitation first using the link from your email"
)


def resolve_user_for_password_login(
    users: Sequence[User],
    password: str,
    *,
    verify_password: Callable[[str, str], bool],
) -> User:
    """Pick the active membership that matches the password."""
    if not users:
        raise InvalidCredentialsError("Invalid email or password")

    active_users = [user for user in users if UserStatus(user.status) == UserStatus.ACTIVE]
    if active_users:
        matching = [
            user
            for user in active_users
            if user.password_hash and verify_password(password, user.password_hash)
        ]
        if len(matching) == 1:
            return matching[0]
        if len(matching) > 1:
            return max(matching, key=lambda user: user.updated_at)
        raise InvalidCredentialsError("Invalid email or password")

    if any(UserStatus(user.status) == UserStatus.INVITED for user in users):
        raise InvalidCredentialsError(_INVITATION_REQUIRED_MESSAGE)

    raise ForbiddenError("Account is not active")


def resolve_user_for_oauth_login(users: Sequence[User]) -> User:
    """Pick the active membership for a Google-authenticated email."""
    if not users:
        raise InvalidCredentialsError("No account found for this Google email")

    active_users = [user for user in users if UserStatus(user.status) == UserStatus.ACTIVE]
    if len(active_users) == 1:
        return active_users[0]
    if len(active_users) > 1:
        return max(active_users, key=lambda user: user.updated_at)

    if any(UserStatus(user.status) == UserStatus.INVITED for user in users):
        raise InvalidCredentialsError(_INVITATION_REQUIRED_MESSAGE)

    raise ForbiddenError("Account is not active")
