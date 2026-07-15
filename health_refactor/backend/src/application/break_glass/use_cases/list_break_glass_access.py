"""Use-case: list break-glass access requests still awaiting super_admin review."""
from backend.src.application.break_glass.commands.list_break_glass_access import (
    ListBreakGlassAccessCommand,
)
from backend.src.application.break_glass.results.list_break_glass_access import (
    BreakGlassAccessSummary,
    ListBreakGlassAccessResult,
)
from backend.src.domain.break_glass.repositories import IBreakGlassAccessRepository


class ListBreakGlassAccess:
    def __init__(self, break_glass_repository: IBreakGlassAccessRepository) -> None:
        self._break_glass_repository = break_glass_repository

    async def execute(
        self, command: ListBreakGlassAccessCommand
    ) -> ListBreakGlassAccessResult:
        requests = await self._break_glass_repository.list_needing_review()
        return ListBreakGlassAccessResult(
            requests=[
                BreakGlassAccessSummary(
                    request_id=r.id,
                    requesting_user_id=r.requesting_user_id,
                    target_patient_id=r.target_patient_id,
                    reason=r.reason,
                    created_at=r.created_at,
                )
                for r in requests
            ]
        )
