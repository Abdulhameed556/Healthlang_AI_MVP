"""OTP storage backed by admin_otps table (no Redis required)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.src.infrastructure.database.models.admin_otp import AdminOtp

OTP_TTL_SECONDS = 600  # 10 minutes


class OTPStore:
    """Stores short-lived login OTPs in Postgres instead of Redis."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(
        self, email: str, otp: str, ttl: int = OTP_TTL_SECONDS
    ) -> None:
        """Upsert an OTP — deletes any existing one for that email first."""
        email = email.strip().lower()
        await self._session.execute(
            delete(AdminOtp).where(AdminOtp.email == email)
        )
        expires = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        self._session.add(
            AdminOtp(id=uuid4(), email=email, otp=otp, expires_at=expires)
        )
        await self._session.flush()

    async def get(self, email: str) -> str | None:
        """Return the OTP for email if it exists and has not expired."""
        email = email.strip().lower()
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            select(AdminOtp.otp).where(
                AdminOtp.email == email,
                AdminOtp.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, email: str) -> None:
        """Remove the OTP after a successful verify."""
        await self._session.execute(
            delete(AdminOtp).where(
                AdminOtp.email == email.strip().lower()
            )
        )
        await self._session.flush()
