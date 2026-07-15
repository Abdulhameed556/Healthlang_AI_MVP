"""
Admin Panel user entity.

This is ENTIRELY SEPARATE from the product dashboard USER table.
Admin Panel users live only in the admin_users table in the admin DB.
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from enum import Enum


class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    READ_ONLY = "read_only"


class AdminUserStatus(str, Enum):
    PENDING = "pending"       # invite sent, not yet accepted
    ACTIVE = "active"
    LOCKED = "locked"         # exceeded failed login attempts


@dataclass
class AdminUser:
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: AdminRole
    status: AdminUserStatus
    password_hash: str | None    # None if Google-OAuth-only
    google_linked: bool
    must_change_password: bool   # True for seeded admin on first login
    failed_attempts: int
    invited_by: UUID | None      # None for seeded admin
    created_at: datetime
    updated_at: datetime
