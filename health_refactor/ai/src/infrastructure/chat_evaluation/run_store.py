"""Run store: in-memory (dev/test) or S3-backed (production)."""
from ai.src.domain.chat_evaluation.entities import ChatEvalReport
from ai.src.domain.chat_evaluation.interfaces import IRunStore

_store: dict[str, ChatEvalReport] = {}


class InMemoryRunStore(IRunStore):
    async def save(self, report: ChatEvalReport) -> None:
        _store[report.run_id] = report

    async def get(self, run_id: str) -> ChatEvalReport | None:
        return _store.get(run_id)

    async def list(
        self,
        agent_id: str | None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ChatEvalReport], int]:
        all_runs = sorted(
            [r for r in _store.values() if r.agent_id == agent_id or agent_id is None],
            key=lambda r: r.created_at or "",
            reverse=True,
        )
        total = len(all_runs)
        start = (page - 1) * page_size
        return all_runs[start : start + page_size], total


_instance: IRunStore | None = None


def get_run_store() -> IRunStore:
    global _instance
    if _instance is None:
        from ai.src.core.config import settings
        if settings.aws_s3_bucket:
            from ai.src.infrastructure.chat_evaluation.s3_run_store import (
                S3RunStore,
            )
            import os
            region = os.getenv("AWS_REGION") or os.getenv(
                "AWS_DEFAULT_REGION", "us-east-1"
            )
            _instance = S3RunStore(
                bucket=settings.aws_s3_bucket, region=region
            )
        else:
            _instance = InMemoryRunStore()
    return _instance
