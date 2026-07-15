"""DeepEval-backed scorers for chat evaluation."""
import asyncio

from ai.src.core.config import settings
from ai.src.domain.chat_evaluation.entities import MetricResult

_DEFAULT_THRESHOLD = 0.7


# ---------------------------------------------------------------------------
# E2E scorer — answer quality metrics
# ---------------------------------------------------------------------------

def _build_e2e_metrics(model: str, threshold: float):
    from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric

    common = dict(model=model, threshold=threshold, async_mode=False)
    return [
        ("answer_relevancy", AnswerRelevancyMetric(**common)),
        ("faithfulness", FaithfulnessMetric(**common)),
    ]


def _score_e2e_sync(
    model: str,
    threshold: float,
    query: str,
    actual_output: str,
    expected_output: str,
    retrieval_context: list[str],
) -> list[MetricResult]:
    from deepeval.test_case import LLMTestCase

    test_case = LLMTestCase(
        input=query,
        actual_output=actual_output,
        expected_output=expected_output,
        retrieval_context=retrieval_context,
    )
    results: list[MetricResult] = []
    for name, metric in _build_e2e_metrics(model, threshold):
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
        except Exception as exc:
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


class E2EScorer:
    def __init__(self, model: str | None = None, threshold: float = _DEFAULT_THRESHOLD) -> None:
        self._model = model or settings.default_judge_model
        self._threshold = threshold

    async def score(
        self,
        query: str,
        actual_output: str,
        expected_output: str,
        retrieval_context: list[str],
    ) -> list[MetricResult]:
        return await asyncio.to_thread(
            _score_e2e_sync,
            self._model,
            self._threshold,
            query,
            actual_output,
            expected_output,
            retrieval_context,
        )


# ---------------------------------------------------------------------------
# KB relevancy scorer — reused for scenario eval KB quality check
# ---------------------------------------------------------------------------

def _score_kb_relevancy_sync(
    model: str,
    threshold: float,
    query: str,
    retrieval_context: list[str],
) -> MetricResult:
    from deepeval.metrics import ContextualRelevancyMetric
    from deepeval.test_case import LLMTestCase

    test_case = LLMTestCase(
        input=query,
        actual_output="",           # not relevant for retrieval-only scoring
        retrieval_context=retrieval_context,
    )
    metric = ContextualRelevancyMetric(model=model, threshold=threshold, async_mode=False)
    try:
        metric.measure(test_case)
        return MetricResult(
            name="kb_relevancy",
            score=float(metric.score or 0.0),
            threshold=threshold,
            success=bool(metric.is_successful()),
            reason=metric.reason or "",
        )
    except Exception as exc:
        return MetricResult(
            name="kb_relevancy",
            score=0.0,
            threshold=threshold,
            success=False,
            reason=f"metric error: {exc}",
        )


class KBRelevancyScorer:
    def __init__(self, model: str | None = None, threshold: float = _DEFAULT_THRESHOLD) -> None:
        self._model = model or settings.default_judge_model
        self._threshold = threshold

    async def score(self, query: str, retrieval_context: list[str]) -> MetricResult:
        return await asyncio.to_thread(
            _score_kb_relevancy_sync,
            self._model,
            self._threshold,
            query,
            retrieval_context,
        )
