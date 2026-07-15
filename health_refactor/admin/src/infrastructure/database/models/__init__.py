"""
SQLAlchemy ORM models for the admin database.

Import every model here so Alembic autogenerate sees full metadata.
"""
from admin.src.infrastructure.database.models.admin_invitation import (
    AdminInvitation,
)
from admin.src.infrastructure.database.models.admin_otp import AdminOtp
from admin.src.infrastructure.database.models.admin_session import AdminSession
from admin.src.infrastructure.database.models.admin_user import AdminUser

__all__ = ["AdminUser", "AdminSession", "AdminInvitation", "AdminOtp"]
