"""Thin Redis cache wrapper for backend infrastructure use-cases."""
from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis


class RedisService:
    """JSON-friendly get/set/delete helpers over an injected Redis client."""

    def __init__(self, client: redis.Redis) -> None:
        self._client = client

    async def ping(self) -> bool:
        """Return True when Redis responds to PING."""
        return bool(await self._client.ping())

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        if ttl_seconds is not None:
            await self._client.setex(key, ttl_seconds, value)
            return
        await self._client.set(key, value)

    async def set_if_absent(
        self,
        key: str,
        value: str,
        *,
        ttl_seconds: int | None = None,
    ) -> bool:
        """Set key only if it does not exist (atomic SET NX). Returns True when set.

        Useful as a claim/lock: the first caller gets True, later callers get
        False until the key expires.
        """
        result = await self._client.set(key, value, nx=True, ex=ttl_seconds)
        return bool(result)

    async def get_json(self, key: str) -> dict[str, Any] | None:
        raw = await self.get(key)
        if raw is None:
            return None
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError(f"Redis value at {key!r} is not a JSON object")
        return data

    async def set_json(
        self,
        key: str,
        value: dict[str, Any],
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        await self.set(key, json.dumps(value), ttl_seconds=ttl_seconds)

    async def delete(self, *keys: str) -> int:
        if not keys:
            return 0
        return int(await self._client.delete(*keys))

    async def delete_by_prefix(self, prefix: str) -> int:
        """Delete all keys that start with prefix."""
        deleted = 0
        async for key in self._client.scan_iter(match=f"{prefix}*"):
            deleted += int(await self._client.delete(key))
        return deleted
