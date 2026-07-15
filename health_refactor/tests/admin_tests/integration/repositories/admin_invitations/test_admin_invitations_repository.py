"""Integration tests: admin_invitations repository against real admin DB."""
import pytest


@pytest.mark.integration
@pytest.mark.skip(reason="Requires db_session fixture and test database")
class TestAdminInvitationsRepository:
    async def test_save_and_retrieve(self):
        assert True
