"""Unit tests: application/auth/use_cases/logout.py"""
from unittest.mock import AsyncMock

import pytest

from backend.src.application.auth.commands.logout import LogoutCommand
from backend.src.application.auth.use_cases.logout import Logout


@pytest.fixture()
def use_case() -> Logout:
    return Logout(session_repository=AsyncMock())


@pytest.mark.asyncio
async def test_execute_invalidates_session_by_token(use_case: Logout) -> None:
    await use_case.execute(LogoutCommand(access_token="  bearer-token  "))

    use_case._session_repository.invalidate_by_token.assert_awaited_once_with(
        "bearer-token"
    )
