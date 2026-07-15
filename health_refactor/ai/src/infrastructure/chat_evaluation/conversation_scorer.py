"""DeepEval GEval-backed scorer for conversation evaluation."""
from __future__ import annotations

import asyncio

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from ai.src.core.config import settings
from ai.src.domain.chat_evaluation.entities import MetricResult

_DEFAULT_THRESHOLD = 0.5

_METRIC_CONFIGS: list[tuple[str, str, list]] = [
    (
        "conversation_quality",
        (
            "Does the agent respond helpfully, coherently, and on-topic "
            "across all turns? Score higher when the agent resolves the "
            "customer's issue clearly and concisely."
        ),
        [LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
    ),
    (
        "kb_utilization",
        (
            "Does the agent reference relevant knowledge base information "
            "in its responses where appropriate? Score higher when the agent "
            "uses product knowledge accurately rather than giving vague or "
            "generic answers."
        ),
        [
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.CONTEXT,
        ],
    ),
    (
        "rule_adherence",
        (
            "Does the agent follow all configured rules throughout the "
            "conversation? Score higher when the agent avoids sensitive data "
            "exposure, stays in scope, and applies any listed policies "
            "correctly."
        ),
        [
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.CONTEXT,
        ],
    ),
]


def _format_conversation(turns: list[dict]) -> str:
    lines: list[str] = []
    for i, turn in enumerate(turns, 1):
        lines.append(f"Turn {i}")
        lines.append(f"  Customer: {turn.get('user', '')}")
        agent = turn.get("agent_actual", turn.get("agent_expected", ""))
        lines.append(f"  Agent: {agent}")
    return "\n".join(lines)


def _score_metric_sync(
    name: str,
    criteria: str,
    params: list,
    model: str,
    threshold: float,
    test_case: LLMTestCase,
) -> MetricResult:
    metric = GEval(
        name=name,
        criteria=criteria,
        evaluation_params=params,
        model=model,
        threshold=threshold,
        async_mode=False,
    )
    try:
        metric.measure(test_case)
        return MetricResult(
            name=name,
            score=float(metric.score or 0.0),
            threshold=threshold,
            success=bool(metric.is_successful()),
            reason=metric.reason or "",
        )
    except Exception as exc:  # noqa: BLE001
        return MetricResult(
            name=name,
            score=0.0,
            threshold=threshold,
            success=False,
            reason=f"metric error: {exc}",
        )


class ConversationScorer:
    def __init__(
        self,
        model: str | None = None,
        threshold: float = _DEFAULT_THRESHOLD,
    ) -> None:
        self._model = model or settings.default_judge_model
        self._threshold = threshold

    async def score(
        self,
        scenario_description: str,
        conversation_turns: list[dict],
        rules: list[str],
        kb_descriptions: list[str],
    ) -> list[MetricResult]:
        conversation_text = _format_conversation(conversation_turns)
        rules_text = "; ".join(rules) if rules else "none"
        kbs_text = "; ".join(kb_descriptions) if kb_descriptions else "none"
        test_case = LLMTestCase(
            input=scenario_description,
            actual_output=conversation_text,
            context=[f"KB descriptions: {kbs_text}", f"Rules: {rules_text}"],
        )
        tasks = [
            asyncio.to_thread(
                _score_metric_sync,
                name,
                criteria,
                params,
                self._model,
                self._threshold,
                test_case,
            )
            for name, criteria, params in _METRIC_CONFIGS
        ]
        raw = await asyncio.gather(*tasks, return_exceptions=True)
        return [
            r
            if isinstance(r, MetricResult)
            else MetricResult(
                name=_METRIC_CONFIGS[i][0],
                score=0.0,
                threshold=self._threshold,
                success=False,
                reason=f"metric error: {r}",
            )
            for i, r in enumerate(raw)
        ]
