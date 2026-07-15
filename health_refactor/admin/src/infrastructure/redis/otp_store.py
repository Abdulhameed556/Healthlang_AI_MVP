"""
OTP storage backed by Redis.

A login OTP is short-lived (10 minutes) and single-use, so Redis with a TTL is a
natural fit — no table or cleanup job needed. Keys are namespaced per email:

    otp:{email}            -> the 6-digit code        (TTL = OTP_TTL_SECONDS)

The store takes a Redis client by injection so it is trivial to unit-test with a
mock. Use :func:`admin.src.infrastructure.redis.client.get_redis` to obtain one.
"""
from __future__ import annotations

import redis.asyncio as redis

OTP_TTL_SECONDS = 600  # 10 minutes


def _key(email: str) -> str:
    return f"otp:{email.strip().lower()}"


class OTPStore:
    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    async def save(self, email: str, otp: str, ttl: int = OTP_TTL_SECONDS) -> None:
        """Store ``otp`` for ``email`` with a time-to-live (seconds)."""
        await self._client.setex(_key(email), ttl, otp)

    async def get(self, email: str) -> str | None:
        """Return the stored OTP for ``email``, or ``None`` if absent/expired."""
        return await self._client.get(_key(email))

    async def delete(self, email: str) -> None:
        """Remove the OTP for ``email`` (called after a successful verify)."""
        await self._client.delete(_key(email))
