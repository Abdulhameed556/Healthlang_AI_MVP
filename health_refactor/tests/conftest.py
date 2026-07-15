"""
Root conftest — sets env defaults for both admin, backend, and AI service
before any module-level Settings() singleton is instantiated during collection.
Also configures a Dramatiq StubBroker so @dramatiq.actor decorators register
without needing a real Redis connection.
"""
import os

import dramatiq
from dramatiq.brokers.stub import StubBroker

# ── Backend ────────────────────────────────────────────────────────────
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost/supportos_test")
os.environ.setdefault("JWT_SECRET_KEY", "test-backend-jwt-secret")
# Force-set (not setdefault) because deepeval loads .env before conftest runs,
# which sets an invalid hex key from .env into os.environ first.
os.environ["API_TOOL_SECRETS_ENCRYPTION_KEY"] = "fk6yOUkVYzXKsRABRnqeSMK6p4tYpBIfrAZcu9jv12s="
os.environ["ADMIN_INTERNAL_API_KEY"] = "test-admin-internal-api-key"

# ── Admin ──────────────────────────────────────────────────────────────
os.environ.setdefault("ADMIN_JWT_SECRET_KEY", "test-admin-jwt-secret")

# ── AI service ─────────────────────────────────────────────────────────
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-api-key")

# Dramatiq — use a stub broker for all tests so @dramatiq.actor decorators
# register without a real Redis connection, and .send() is a no-op.
dramatiq.set_broker(StubBroker())
