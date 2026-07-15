"""Unit tests: application/break_glass/use_cases/review_break_glass_access.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.break_glass.commands.review_break_glass_access import (
    ReviewBreakGlassAccessCommand,
)
from backend.src.application.break_glass.use_cases.review_break_glass_access import (
    ReviewBreakGlassAccess,
)
from backend.src.domain.break_glass.entities import BreakGlassAccess
from backend.src.domain.break_glass.exceptions import BreakGlassAccessNotFoundError


def _request() -> BreakGlassAccess:
    return BreakGlassAccess(
        id=uuid4(),
        requesting_user_id=uuid4(),
        target_patient_id=uuid4(),
        reason="Emergency coverage",
        needs_review=True,
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_execute_marks_reviewed() -> None:
    repo = AsyncMock()
    request = _request()
    repo.get_by_id = AsyncMock(return_value=request)
    repo.save = AsyncMock(side_effect=lambda r: r)
    unit_of_work = AsyncMock()
    unit_of_work.commit = AsyncMock()
    use_case = ReviewBreakGlassAccess(break_glass_repository=repo, unit_of_work=unit_of_work)
    reviewer_id = uuid4()

    result = await use_case.execute(
        ReviewBreakGlassAccessCommand(request_id=request.id, reviewed_by=reviewer_id)
    )

    assert result.needs_review is False
    assert result.reviewed_by == reviewer_id
    unit_of_work.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_raises_when_missing() -> None:
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    use_case = ReviewBreakGlassAccess(break_glass_repository=repo, unit_of_work=AsyncMock())

    with pytest.raises(BreakGlassAccessNotFoundError):
        await use_case.execute(
            ReviewBreakGlassAccessCommand(request_id=uuid4(), reviewed_by=uuid4())
        )
