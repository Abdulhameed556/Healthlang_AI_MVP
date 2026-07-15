"""Unit tests: Redis OTP store + client factory."""
from unittest.mock import AsyncMock

from admin.src.infrastructure.redis import client as client_mod
from admin.src.infrastructure.redis.otp_store import OTP_TTL_SECONDS, OTPStore


class TestOTPStore:
    async def test_save_uses_setex_with_ttl_and_normalised_key(self):
        redis = AsyncMock()
        store = OTPStore(redis)
        await store.save("  Admin@Example.COM ", "123456")
        redis.setex.assert_awaited_once_with(
            "otp:admin@example.com", OTP_TTL_SECONDS, "123456"
        )

    async def test_save_custom_ttl(self):
        redis = AsyncMock()
        await OTPStore(redis).save("a@b.com", "111111", ttl=30)
        redis.setex.assert_awaited_once_with("otp:a@b.com", 30, "111111")

    async def test_get_returns_value(self):
        redis = AsyncMock()
        redis.get.return_value = "123456"
        result = await OTPStore(redis).get("a@b.com")
        assert result == "123456"
        redis.get.assert_awaited_once_with("otp:a@b.com")

    async def test_delete(self):
        redis = AsyncMock()
        await OTPStore(redis).delete("a@b.com")
        redis.delete.assert_awaited_once_with("otp:a@b.com")


class TestRedisClientFactory:
    async def test_get_redis_is_singleton_then_close(self):
        await client_mod.close_redis()  # clean slate
        first = client_mod.get_redis()
        second = client_mod.get_redis()
        assert first is second
        await client_mod.close_redis()
        assert client_mod._client is None

    async def test_close_when_already_closed_is_noop(self):
        await client_mod.close_redis()
        await client_mod.close_redis()  # must not raise
        assert client_mod._client is None
