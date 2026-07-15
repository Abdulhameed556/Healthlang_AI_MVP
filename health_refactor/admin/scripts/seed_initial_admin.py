"""
Seed the initial Admin Panel admin account.

Run at deploy time when the admin_users table is empty.
Credentials come from SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD in .env.
The seeded account has must_change_password=True — user is prompted
to set a new password on first login.

Usage:
    python scripts/seed_initial_admin.py
    make seed

Guard: if any admin user already exists in the database, the script
exits without making any changes.
"""
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

# Allow running as: python scripts/seed_initial_admin.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from admin.src.core.config import settings
from admin.src.core.security import hash_password
from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus
from admin.src.infrastructure.database.session import async_session_factory
from admin.src.infrastructure.repositories.admin_users import AdminUserRepository


async def seed_initial_admin() -> None:
    email = settings.seed_admin_email.strip().lower()
    password = settings.seed_admin_password

    if not email or not password:
        print("Error: SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD must be set in .env")
        sys.exit(1)

    async with async_session_factory() as session:
        repo = AdminUserRepository(session)

        if await repo.count_all() > 0:
            print("Admin users already exist — skipping seed.")
            return

        now = datetime.now(timezone.utc)
        admin = AdminUser(
            id=uuid4(),
            email=email,
            first_name="Platform",
            last_name="Admin",
            role=AdminRole.SUPER_ADMIN,
            status=AdminUserStatus.ACTIVE,
            password_hash=hash_password(password),
            google_linked=False,
            must_change_password=True,
            failed_attempts=0,
            invited_by=None,
            created_at=now,
            updated_at=now,
        )

        await repo.save(admin)
        await session.commit()

        print(f"Seeded initial admin: {email}")


def main() -> None:
    asyncio.run(seed_initial_admin())


if __name__ == "__main__":
    main()
