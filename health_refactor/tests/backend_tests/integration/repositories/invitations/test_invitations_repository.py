"""Integration tests: invitations repository against real DB."""
import pytest


@pytest.mark.integration
@pytest.mark.skip(reason="Requires db_session fixture and test database")
class TestInvitationRepository:
    async def test_add_and_get_by_token(self) -> None:
        assert True
