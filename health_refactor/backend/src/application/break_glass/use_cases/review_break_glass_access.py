"""Use-case: super_admin marks a break-glass access request as reviewed."""
from dataclasses import replace
from datetime import datetime, timezone

from backend.src.application.break_glass.commands.review_break_glass_access import (
    ReviewBreakGlassAccessCommand,
)
from backend.src.application.break_glass.results.review_break_glass_access import (
    ReviewBreakGlassAccessResult,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.break_glass.exceptions import BreakGlassAccessNotFoundError
from backend.src.domain.break_glass.repositories import IBreakGlassAccessRepository


class ReviewBreakGlassAccess:
    def __init__(
        self,
        break_glass_repository: IBreakGlassAccessRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._break_glass_repository = break_glass_repository
        self._unit_of_work = unit_of_work

    async def execute(
        self, command: ReviewBreakGlassAccessCommand
    ) -> ReviewBreakGlassAccessResult:
        request = await self._break_glass_repository.get_by_id(command.request_id)
        if request is None:
            raise BreakGlassAccessNotFoundError("Break-glass access request not found")

        now = datetime.now(timezone.utc)
        updated = replace(
            request,
            needs_review=False,
            reviewed_by=command.reviewed_by,
            reviewed_at=now,
        )
        updated = await self._break_glass_repository.save(updated)
        await self._unit_of_work.commit()

        return ReviewBreakGlassAccessResult(
            request_id=updated.id,
            needs_review=updated.needs_review,
            reviewed_by=updated.reviewed_by,
            reviewed_at=updated.reviewed_at,
        )
