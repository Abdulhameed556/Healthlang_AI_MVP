"""Unit tests: application/break_glass/use_cases/list_break_glass_access.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.break_glass.commands.list_break_glass_access import (
    ListBreakGlassAccessCommand,
)
from backend.src.application.break_glass.use_cases.list_break_glass_access import (
    ListBreakGlassAccess,
)
from backend.src.domain.break_glass.entities import BreakGlassAccess


@pytest.mark.asyncio
async def test_execute_returns_requests_needing_review() -> None:
    repo = AsyncMock()
    request = BreakGlassAccess(
        id=uuid4(),
        requesting_user_id=uuid4(),
        target_patient_id=uuid4(),
        reason="Emergency coverage",
        needs_review=True,
        created_at=datetime.now(timezone.utc),
    )
    repo.list_needing_review = AsyncMock(return_value=[request])
    use_case = ListBreakGlassAccess(break_glass_repository=repo)

    result = await use_case.execute(ListBreakGlassAccessCommand())

    assert len(result.requests) == 1
    assert result.requests[0].reason == "Emergency coverage"


@pytest.mark.asyncio
async def test_execute_returns_empty_when_none_pending() -> None:
    repo = AsyncMock()
    repo.list_needing_review = AsyncMock(return_value=[])
    use_case = ListBreakGlassAccess(break_glass_repository=repo)

    result = await use_case.execute(ListBreakGlassAccessCommand())

    assert result.requests == []
