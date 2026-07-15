"""Interfaces for retrieval evaluation — the application depends only on these."""
from typing import Protocol

from ai.src.domain.retrieval_evaluation.entities import (
    EvaluationReport,
    MetricResult,
    RetrievalGolden,
)


class ITestsetSynthesizer(Protocol):
    """Generate question/expected-answer goldens from KB document contexts."""

    async def synthesize(
        self, contexts: list[list[str]], max_per_context: int
    ) -> list[RetrievalGolden]: ...


class IRetrievalScorer(Protocol):
    """Score one RAG test case with the configured DeepEval metrics."""

    async def score(
        self,
        question: str,
        actual_output: str,
        expected_output: str,
        retrieval_context: list[str],
    ) -> list[MetricResult]: ...


class IEvaluationRunStore(Protocol):
    """Persistence for evaluation runs so status can be polled."""

    async def save(self, report: EvaluationReport) -> None: ...

    async def get(self, run_id: str) -> EvaluationReport | None: ...
