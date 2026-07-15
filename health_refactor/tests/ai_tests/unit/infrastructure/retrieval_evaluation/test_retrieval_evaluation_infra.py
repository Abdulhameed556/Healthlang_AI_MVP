"""Unit tests: ai/src/infrastructure/retrieval_evaluation/*"""
from unittest.mock import MagicMock, patch

import pytest


# ── DeepEvalSynthesizer ───────────────────────────────────────────────────────


def test_synthesize_sync_maps_goldens() -> None:
    from ai.src.infrastructure.retrieval_evaluation import synthesizer as mod

    golden = MagicMock(input="Q?", expected_output="A.", context=["c1", "c2"])
    fake_synth = MagicMock()
    fake_synth.generate_goldens_from_contexts.return_value = [golden]

    # Synthesizer is imported lazily inside _synthesize_sync — patch at source.
    with patch("deepeval.synthesizer.Synthesizer", return_value=fake_synth) as synth_cls:
        result = mod._synthesize_sync("gpt-4o", [["c1", "c2"]], 2)

    synth_cls.assert_called_once_with(model="gpt-4o")
    assert len(result) == 1
    assert result[0].question == "Q?"
    assert result[0].expected_output == "A."
    assert result[0].source_context == ["c1", "c2"]


@pytest.mark.asyncio
async def test_synthesizer_returns_empty_for_no_contexts() -> None:
    from ai.src.infrastructure.retrieval_evaluation.synthesizer import DeepEvalSynthesizer

    result = await DeepEvalSynthesizer(model="gpt-4o").synthesize([], 2)
    assert result == []


@pytest.mark.asyncio
async def test_synthesizer_delegates_to_thread(monkeypatch) -> None:
    from ai.src.infrastructure.retrieval_evaluation import synthesizer as mod

    monkeypatch.setattr(
        mod, "_synthesize_sync", lambda model, contexts, n: ["golden"]
    )
    result = await mod.DeepEvalSynthesizer(model="gpt-4o").synthesize([["c"]], 1)
    assert result == ["golden"]


# ── DeepEvalScorer ────────────────────────────────────────────────────────────


def test_score_sync_collects_metric_results() -> None:
    from ai.src.infrastructure.retrieval_evaluation import scorer as mod

    metric = MagicMock()
    metric.score = 0.85
    metric.is_successful.return_value = True
    metric.reason = "looks good"

    with patch.object(mod, "_build_metrics", return_value=[("contextual_relevancy", metric)]):
        results = mod._score_sync("gpt-4o", 0.7, "q", "a", "e", ["ctx"])

    assert len(results) == 1
    assert results[0].name == "contextual_relevancy"
    assert results[0].score == 0.85
    assert results[0].success is True
    assert results[0].reason == "looks good"
    metric.measure.assert_called_once()


def test_score_sync_isolates_metric_failure() -> None:
    from ai.src.infrastructure.retrieval_evaluation import scorer as mod

    bad = MagicMock()
    bad.measure.side_effect = RuntimeError("judge timeout")

    with patch.object(mod, "_build_metrics", return_value=[("contextual_precision", bad)]):
        results = mod._score_sync("gpt-4o", 0.7, "q", "a", "e", ["ctx"])

    assert results[0].success is False
    assert results[0].score == 0.0
    assert "judge timeout" in results[0].reason


@pytest.mark.asyncio
async def test_scorer_delegates_to_thread(monkeypatch) -> None:
    from ai.src.infrastructure.retrieval_evaluation import scorer as mod

    monkeypatch.setattr(
        mod, "_score_sync", lambda *a: ["m"]
    )
    result = await mod.DeepEvalScorer(model="gpt-4o").score("q", "a", "e", ["c"])
    assert result == ["m"]


def test_build_metrics_returns_three(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    from ai.src.infrastructure.retrieval_evaluation.scorer import _build_metrics

    metrics = _build_metrics("gpt-4o", 0.7)
    names = [name for name, _ in metrics]
    assert names == [
        "contextual_relevancy",
        "contextual_precision",
        "contextual_recall",
    ]


# ── InMemoryEvaluationRunStore ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_store_save_and_get() -> None:
    from ai.src.domain.retrieval_evaluation.entities import EvaluationReport
    from ai.src.infrastructure.retrieval_evaluation.run_store import (
        InMemoryEvaluationRunStore,
    )
    from uuid import uuid4

    store = InMemoryEvaluationRunStore()
    report = EvaluationReport(run_id="r1", agent_id=uuid4(), kb_entry_id=uuid4())
    await store.save(report)

    assert await store.get("r1") is report
    assert await store.get("missing") is None


def test_get_run_store_returns_singleton() -> None:
    from ai.src.infrastructure.retrieval_evaluation.run_store import get_run_store

    assert get_run_store() is get_run_store()
