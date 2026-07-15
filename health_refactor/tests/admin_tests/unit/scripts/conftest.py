"""Env defaults for loading seed script during tests."""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost/admin_panel_test")
os.environ.setdefault("ADMIN_JWT_SECRET_KEY", "test-jwt-secret-for-unit-tests")
