"""Unit tests: scripts/seed_initial_admin.py"""
import importlib.util
from pathlib import Path

import pytest

from admin.src.domain.users.entities import AdminRole, AdminUser, AdminUserStatus

SEED_SCRIPT = (
    Path(__file__).resolve().parents[4] / "admin" / "scripts" / "seed_initial_admin.py"
)


def _load_seed_module():
    spec = importlib.util.spec_from_file_location("seed_initial_admin", SEED_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestSeedInitialAdminGuard:
    @pytest.mark.asyncio
    async def test_skips_when_admin_users_exist(self, monkeypatch):
        seed = _load_seed_module()
        calls = {"save": 0}

        class FakeRepo:
            async def count_all(self) -> int:
                return 1

            async def save(self, user: AdminUser) -> AdminUser:
                calls["save"] += 1
                return user

        class FakeSession:
            async def commit(self) -> None:
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        monkeypatch.setattr(seed.settings, "seed_admin_email", "admin@platform.com")
        monkeypatch.setattr(seed.settings, "seed_admin_password", "secret")
        monkeypatch.setattr(seed, "async_session_factory", lambda: FakeSession())
        monkeypatch.setattr(seed, "AdminUserRepository", lambda session: FakeRepo())

        await seed.seed_initial_admin()

        assert calls["save"] == 0

    @pytest.mark.asyncio
    async def test_creates_admin_when_table_empty(self, monkeypatch):
        seed = _load_seed_module()
        saved: list[AdminUser] = []

        class FakeRepo:
            async def count_all(self) -> int:
                return 0

            async def save(self, user: AdminUser) -> AdminUser:
                saved.append(user)
                return user

        class FakeSession:
            async def commit(self) -> None:
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        monkeypatch.setattr(seed.settings, "seed_admin_email", "admin@platform.com")
        monkeypatch.setattr(seed.settings, "seed_admin_password", "secret")
        monkeypatch.setattr(seed, "hash_password", lambda plain: f"hashed:{plain}")
        monkeypatch.setattr(seed, "async_session_factory", lambda: FakeSession())
        monkeypatch.setattr(seed, "AdminUserRepository", lambda session: FakeRepo())

        await seed.seed_initial_admin()

        assert len(saved) == 1
        assert saved[0].email == "admin@platform.com"
        assert saved[0].role == AdminRole.SUPER_ADMIN
        assert saved[0].status == AdminUserStatus.ACTIVE
        assert saved[0].must_change_password is True
        assert saved[0].password_hash == "hashed:secret"
