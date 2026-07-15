"""DeepEval-backed test-set synthesizer.

Turns groups of KB document chunks into question/expected-answer goldens.
"""
import asyncio

from ai.src.core.config import settings
from ai.src.domain.retrieval_evaluation.entities import RetrievalGolden


def _synthesize_sync(
    model: str, contexts: list[list[str]], max_per_context: int
) -> list[RetrievalGolden]:
    from deepeval.synthesizer import Synthesizer

    synthesizer = Synthesizer(model=model)
    goldens = synthesizer.generate_goldens_from_contexts(
        contexts=contexts,
        include_expected_output=True,
        max_goldens_per_context=max_per_context,
    )
    return [
        RetrievalGolden(
            question=g.input,
            expected_output=g.expected_output or "",
            source_context=list(g.context or []),
        )
        for g in goldens
    ]


class DeepEvalSynthesizer:
    def __init__(self, model: str | None = None) -> None:
        self._model = model or settings.default_judge_model

    async def synthesize(
        self, contexts: list[list[str]], max_per_context: int = 2
    ) -> list[RetrievalGolden]:
        if not contexts:
            return []
        return await asyncio.to_thread(
            _synthesize_sync, self._model, contexts, max_per_context
        )
