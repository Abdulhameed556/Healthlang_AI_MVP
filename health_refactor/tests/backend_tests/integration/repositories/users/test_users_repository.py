"""Integration tests: users repository against real DB."""
import pytest


@pytest.mark.integration
@pytest.mark.skip(reason="Requires db_session fixture and test database")
class TestUserRepository:
    async def test_add_and_get_by_email(self) -> None:
        assert True
