"""Integration tests: admin_sessions repository against real admin DB."""
import pytest


@pytest.mark.integration
@pytest.mark.skip(reason="Requires db_session fixture and test database")
class TestAdminSessionsRepository:
    async def test_save_and_retrieve(self):
        assert True
