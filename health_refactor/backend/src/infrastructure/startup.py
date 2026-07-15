"""Fail-fast checks for required infrastructure at process startup."""
from __future__ import annotations

import logging

from backend.src.infrastructure.database.session import verify_database_connection
from backend.src.infrastructure.redis.client import verify_redis_connection

logger = logging.getLogger(__name__)


async def verify_required_dependencies() -> None:
    """Verify Postgres and Redis are reachable; abort startup on failure."""
    try:
        logger.info("Verifying database connection...")
        await verify_database_connection()
        logger.info("Database connection OK")
    except Exception:
        logger.exception("Database connection failed at startup")
        raise

    try:
        logger.info("Verifying Redis connection...")
        await verify_redis_connection()
        logger.info("Redis connection OK")
    except Exception:
        logger.exception("Redis connection failed at startup")
        raise
