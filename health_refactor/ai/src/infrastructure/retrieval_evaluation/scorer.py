"""DeepEval-backed RAG scorer — runs retrieval-only metrics."""
import asyncio

from ai.src.core.config import settings
from ai.src.domain.retrieval_evaluation.entities import MetricResult

_DEFAULT_THRESHOLD = 0.7


def _build_metrics(model: str, threshold: float):
    from deepeval.metrics import (
        ContextualPrecisionMetric,
        ContextualRecallMetric,
        ContextualRelevancyMetric,
    )

    common = dict(model=model, threshold=threshold, async_mode=False)
    return [
        ("contextual_relevancy", ContextualRelevancyMetric(**common)),
        ("contextual_precision", ContextualPrecisionMetric(**common)),
        ("contextual_recall", ContextualRecallMetric(**common)),
    ]


def _score_sync(
    model: str,
    threshold: float,
    question: str,
    actual_output: str,
    expected_output: str,
    retrieval_context: list[str],
) -> list[MetricResult]:
    from deepeval.test_case import LLMTestCase

    test_case = LLMTestCase(
        input=question,
        actual_output=actual_output,
        expected_output=expected_output,
        retrieval_context=retrieval_context,
    )
    results: list[MetricResult] = []
    for name, metric in _build_metrics(model, threshold):
        try:
            metric.measure(test_case)
            results.append(
                MetricResult(
                    name=name,
                    score=float(metric.score or 0.0),
                    threshold=threshold,
                    success=bool(metric.is_successful()),
                    reason=metric.reason or "",
                )
            )
        except Exception as exc:  # one metric failing must not abort the rest
            results.append(
                MetricResult(
                    name=name,
                    score=0.0,
                    threshold=threshold,
                    success=False,
                    reason=f"metric error: {exc}",
                )
            )
    return results


class DeepEvalScorer:
    def __init__(
        self, model: str | None = None, threshold: float = _DEFAULT_THRESHOLD
    ) -> None:
        self._model = model or settings.default_judge_model
        self._threshold = threshold

    async def score(
        self,
        question: str,
        actual_output: str,
        expected_output: str,
        retrieval_context: list[str],
    ) -> list[MetricResult]:
        return await asyncio.to_thread(
            _score_sync,
            self._model,
            self._threshold,
            question,
            actual_output,
            expected_output,
            retrieval_context,
        )
