"""Step: group source chunks into contexts and synthesize golden test cases."""
from ai.src.application.retrieval_evaluation.context import RetrievalEvaluationContext
from ai.src.domain.retrieval_evaluation.interfaces import ITestsetSynthesizer


def _group_chunks(chunks: list[str], per_group: int, max_groups: int) -> list[list[str]]:
    groups: list[list[str]] = []
    for i in range(0, len(chunks), per_group):
        groups.append(chunks[i : i + per_group])
        if len(groups) >= max_groups:
            break
    return groups


class SynthesizeTestsetStep:
    def __init__(self, synthesizer: ITestsetSynthesizer) -> None:
        self._synthesizer = synthesizer

    async def run(self, ctx: RetrievalEvaluationContext) -> None:
        contexts = _group_chunks(
            ctx.source_chunks, ctx.chunks_per_context, ctx.max_contexts
        )
        ctx.goldens = await self._synthesizer.synthesize(
            contexts, ctx.max_goldens_per_context
        )
