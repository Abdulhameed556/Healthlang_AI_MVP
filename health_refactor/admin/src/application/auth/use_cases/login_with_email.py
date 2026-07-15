"""Use-case: Login With Email (two-step: password -> OTP -> token).

Flow:
    initiate(email, password)
        validate credentials, enforce lockout, issue + email an OTP.
    verify(email, otp)
        check the OTP, issue a 60-minute JWT, persist a server-side session.

Failed-password attempts are persisted (committed) even though the call then
raises, so the lockout counter accumulates across separate requests.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from admin.src.core.config import settings
from admin.src.core.exceptions import AccountLockedError, UnauthorizedError
from admin.src.core.security import create_access_token, hash_token, verify_password
from admin.src.domain.auth.entities import AdminSession
from admin.src.domain.users.entities import AdminUserStatus

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from admin.src.domain.auth.repositories import IAdminSessionRepository
    from admin.src.domain.users.repositories import IAdminUserRepository
    from admin.src.infrastructure.email.client import EmailClient
    from admin.src.infrastructure.redis.otp_store import OTPStore

_INVALID_CREDENTIALS = "Invalid email or password"


def _generate_otp() -> str:
    """Six-digit OTP. Fixed to 123456 in development for easy testing."""
    if settings.app_env == "development":
        return "123456"
    return f"{secrets.randbelow(1_000_000):06d}"


class LoginWithEmailUseCase:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: IAdminUserRepository,
        session_repo: IAdminSessionRepository,
        otp_store: OTPStore,
        email_client: EmailClient,
    ) -> None:
        self._session = session
        self._users = user_repo
        self._sessions = session_repo
        self._otp = otp_store
        self._email = email_client

    async def initiate(self, email: str, password: str) -> None:
        user = await self._users.get_by_email(email)
        # Generic error everywhere below to avoid leaking which emails exist.
        if user is None or user.password_hash is None:
            raise UnauthorizedError(_INVALID_CREDENTIALS)
        if user.status == AdminUserStatus.LOCKED:
            raise AccountLockedError("Account is locked")
        if user.status != AdminUserStatus.ACTIVE:
            raise UnauthorizedError(_INVALID_CREDENTIALS)

        if not verify_password(password, user.password_hash):
            await self._register_failure(user)

        # Successful password — clear any prior failures, then send the OTP.
        if user.failed_attempts:
            user.failed_attempts = 0
            await self._users.save(user)
            await self._session.commit()

        otp = _generate_otp()
        await self._otp.save(email, otp)
        await self._email.send_otp_email(email, otp)

    async def _register_failure(self, user) -> None:
        """Increment the counter, lock at the threshold, persist, then raise."""
        user.failed_attempts += 1
        threshold = settings.max_failed_login_attempts
        locked = user.failed_attempts >= threshold
        if locked:
            user.status = AdminUserStatus.LOCKED
        await self._users.save(user)
        await self._session.commit()
        if locked:
            raise AccountLockedError("Account is locked")
        raise UnauthorizedError(_INVALID_CREDENTIALS)

    async def verify(self, email: str, otp: str) -> tuple[str, bool]:
        stored = await self._otp.get(email)
        if stored is None:
            raise UnauthorizedError("OTP expired or not found")
        if not secrets.compare_digest(stored, otp):
            raise UnauthorizedError("Invalid OTP")
        await self._otp.delete(email)

        user = await self._users.get_by_email(email)
        if user is None:
            raise UnauthorizedError(_INVALID_CREDENTIALS)

        token = create_access_token(str(user.id), {"role": user.role.value})
        now = datetime.now(timezone.utc)
        expires = now + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
        await self._sessions.save(
            AdminSession(
                id=uuid4(),
                user_id=user.id,
                token=hash_token(token),
                created_at=now,
                expires_at=expires,
                invalidated_at=None,
            )
        )
        await self._session.commit()
        return token, user.must_change_password
