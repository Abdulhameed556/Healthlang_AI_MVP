"""In-memory evaluation run store.

Process-local; sufficient for single-process dev/demo and status polling.
Swap for a Redis/DB-backed implementation behind IEvaluationRunStore in prod.
"""
import asyncio

from ai.src.domain.retrieval_evaluation.entities import BatchEvaluationReport


class InMemoryEvaluationRunStore:
    def __init__(self) -> None:
        self._runs: dict[str, BatchEvaluationReport] = {}
        self._lock = asyncio.Lock()

    async def save(self, report: BatchEvaluationReport) -> None:
        async with self._lock:
            self._runs[report.run_id] = report

    async def get(self, run_id: str) -> BatchEvaluationReport | None:
        async with self._lock:
            return self._runs.get(run_id)


# Module-level singleton so the API endpoint and background task share state.
_store = InMemoryEvaluationRunStore()


def get_run_store() -> InMemoryEvaluationRunStore:
    return _store
