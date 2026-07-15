"""Orchestrator for the KB retrieval-evaluation pipeline."""
from ai.src.application.retrieval_evaluation.context import RetrievalEvaluationContext
from ai.src.domain.retrieval_evaluation.entities import (
    EvaluationReport,
    QuestionResult,
    RunStatus,
)
from ai.src.domain.retrieval_evaluation.interfaces import IEvaluationRunStore


def _aggregate(question_results: list[QuestionResult]) -> dict[str, float]:
    """Mean score per metric across all questions."""
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for qr in question_results:
        for metric in qr.metrics:
            totals[metric.name] = totals.get(metric.name, 0.0) + metric.score
            counts[metric.name] = counts.get(metric.name, 0) + 1
    return {name: totals[name] / counts[name] for name in totals if counts[name]}


class RetrievalEvaluationPipeline:
    def __init__(self, steps: list, run_store: IEvaluationRunStore) -> None:
        self._steps = steps
        self._store = run_store

    async def run(self, ctx: RetrievalEvaluationContext) -> EvaluationReport:
        report = EvaluationReport(
            run_id=ctx.run_id,
            agent_id=ctx.agent_id,
            kb_entry_id=ctx.kb_entry_id,
            status=RunStatus.RUNNING,
        )
        await self._store.save(report)
        try:
            for step in self._steps:
                await step.run(ctx)
            report.question_results = ctx.question_results
            report.aggregate_scores = _aggregate(ctx.question_results)
            report.status = RunStatus.COMPLETED
        except Exception as exc:
            report.status = RunStatus.FAILED
            report.error = str(exc)
        await self._store.save(report)
        return report
