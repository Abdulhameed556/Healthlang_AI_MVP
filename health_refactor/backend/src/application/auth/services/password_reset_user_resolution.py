"""Resolve which user row should receive a password reset email."""
from collections.abc import Sequence

from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserStatus


def resolve_user_for_password_reset(users: Sequence[User]) -> User | None:
    """Pick an active email/password user eligible for password reset."""
    eligible = [
        user
        for user in users
        if UserStatus(user.status) == UserStatus.ACTIVE
        and UserAuthMethod(user.auth_method) == UserAuthMethod.EMAIL_PASSWORD
    ]
    if not eligible:
        return None
    if len(eligible) == 1:
        return eligible[0]
    return max(eligible, key=lambda user: user.updated_at)
