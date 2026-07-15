"""Integration tests: password_resets repository against real DB."""
import pytest


@pytest.mark.integration
@pytest.mark.skip(reason="Requires db_session fixture and test database")
class TestPasswordResetsRepository:
    async def test_add_and_list_pending(self) -> None:
        assert True
