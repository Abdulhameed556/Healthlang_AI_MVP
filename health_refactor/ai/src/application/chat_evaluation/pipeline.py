"""Orchestrator for the chat evaluation pipeline."""
from ai.src.application.chat_evaluation.context import ChatEvalContext
from ai.src.domain.chat_evaluation.entities import (
    ConversationCaseResult,
    EvalMode,
    GuardrailCaseResult,
    OutputGuardrailCaseResult,
    ScenarioCaseResult,
    E2ETurnResult,
    ChatEvalReport,
    RunStatus,
)
from ai.src.domain.chat_evaluation.interfaces import IRunStore


def _aggregate(eval_mode: str, results: list) -> dict[str, float]:
    if not results:
        return {}

    if eval_mode == EvalMode.INPUT_GUARDRAIL:
        return _aggregate_guardrail(results)
    if eval_mode == EvalMode.SCENARIO:
        return _aggregate_scenario(results)
    if eval_mode == EvalMode.OUTPUT_GUARDRAIL:
        return _aggregate_output_guardrail(results)
    if eval_mode == EvalMode.E2E:
        return _aggregate_e2e(results)
    if eval_mode == EvalMode.CONVERSATION:
        return _aggregate_conversation(results)
    return {}


def _aggregate_guardrail(results: list[GuardrailCaseResult]) -> dict[str, float]:
    total = len(results)
    correct = sum(1 for r in results if r.correct)
    safe_cases = [r for r in results if not r.expected_blocked]
    attack_cases = [r for r in results if r.expected_blocked]
    fp = sum(1 for r in safe_cases if r.actual_status == "block")
    fn = sum(1 for r in attack_cases if r.actual_status != "block")
    scores: dict[str, float] = {"accuracy": correct / total}
    if safe_cases:
        scores["false_positive_rate"] = fp / len(safe_cases)
    if attack_cases:
        scores["false_negative_rate"] = fn / len(attack_cases)
    return scores


def _aggregate_scenario(results: list[ScenarioCaseResult]) -> dict[str, float]:
    total = len(results)
    scenario_correct = sum(1 for r in results if r.scenario_correct)
    kb_scores = [
        r.kb_relevancy_score
        for r in results
        if r.kb_relevancy_score is not None
    ]
    kb_selected = sum(1 for r in results if r.kb_id_selected is not None)
    scores: dict[str, float] = {
        "scenario_accuracy": scenario_correct / total,
        "kb_selection_rate": kb_selected / total,
    }
    if kb_scores:
        scores["kb_relevancy_mean"] = sum(kb_scores) / len(kb_scores)
    return scores


def _aggregate_output_guardrail(
    results: list[OutputGuardrailCaseResult],
) -> dict[str, float]:
    total = len(results)
    correct = sum(1 for r in results if r.correct)
    return {"action_accuracy": correct / total}


def _aggregate_e2e(results: list[E2ETurnResult]) -> dict[str, float]:
    scores: dict[str, list[float]] = {}
    for result in results:
        for metric in result.metrics:
            scores.setdefault(metric.name, []).append(metric.score)
    return {
        name: sum(vals) / len(vals)
        for name, vals in scores.items()
        if vals
    }


def _aggregate_conversation(
    results: list[ConversationCaseResult],
) -> dict[str, float]:
    metric_buckets: dict[str, list[float]] = {}
    scenario_ids: set[str] = set()
    for result in results:
        scenario_ids.add(result.scenario_id)
        for metric_name, score in result.scores.items():
            metric_buckets.setdefault(metric_name, []).append(score)

    scores: dict[str, float] = {
        name: sum(vals) / len(vals)
        for name, vals in metric_buckets.items()
        if vals
    }
    scores["scenarios_covered"] = float(len(scenario_ids))

    # Judge score — mean of all per-criterion scores across all results.
    # Only present when judge_criteria were configured and scoring succeeded.
    all_judge_scores: list[float] = [
        entry["score"]
        for r in results
        for entry in r.judge_scores.values()
        if isinstance(entry, dict) and "score" in entry
    ]
    if all_judge_scores:
        scores["judge_score"] = (
            sum(all_judge_scores) / len(all_judge_scores)
        )

    # Consistency score: only meaningful when determinism_runs > 1.
    # Groups results by (scenario_id, persona), then measures average
    # score range across runs (0 = maximally inconsistent, 1 = identical).
    groups: dict[tuple, list[ConversationCaseResult]] = {}
    for r in results:
        key = (r.scenario_id, r.persona)
        groups.setdefault(key, []).append(r)
    multi_run_groups = [g for g in groups.values() if len(g) > 1]
    if multi_run_groups:
        ranges: list[float] = []
        for group in multi_run_groups:
            metric_names = set(
                m for r in group for m in r.scores
            )
            for m in metric_names:
                vals = [r.scores[m] for r in group if m in r.scores]
                if len(vals) > 1:
                    ranges.append(max(vals) - min(vals))
        if ranges:
            scores["response_consistency"] = (
                1.0 - sum(ranges) / len(ranges)
            )
    return scores


class ChatEvaluationPipeline:
    def __init__(self, steps: list, run_store: IRunStore) -> None:
        self._steps = steps
        self._store = run_store

    async def run(self, ctx: ChatEvalContext) -> ChatEvalReport:
        report = ChatEvalReport(
            run_id=ctx.run_id,
            eval_mode=ctx.eval_mode,
            agent_id=ctx.agent_id,
            status=RunStatus.RUNNING,
        )
        await self._store.save(report)
        try:
            for step in self._steps:
                await step.run(ctx)
            report.case_results = ctx.results
            report.aggregate_scores = _aggregate(ctx.eval_mode, ctx.results)
            report.status = RunStatus.COMPLETED
        except Exception as exc:  # noqa: BLE001
            report.status = RunStatus.FAILED
            report.error = str(exc)
        await self._store.save(report)
        return report
