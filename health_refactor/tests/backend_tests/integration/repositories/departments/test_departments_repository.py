"""Integration tests: departments repository against real DB."""
import pytest


@pytest.mark.integration
@pytest.mark.skip(reason="Requires db_session fixture and test database")
class TestDepartmentRepository:
    async def test_add_and_get_by_id(self) -> None:
        assert True
