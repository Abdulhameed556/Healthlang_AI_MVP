"""Step: for each golden, retrieve chunks → score retrieval metrics."""
from ai.src.application.retrieval_evaluation.context import RetrievalEvaluationContext
from ai.src.domain.retrieval_evaluation.entities import QuestionResult
from ai.src.domain.retrieval_evaluation.interfaces import IRetrievalScorer


class RunTestCasesStep:
    def __init__(self, retrieval_pipeline, scorer: IRetrievalScorer) -> None:
        self._retrieval = retrieval_pipeline
        self._scorer = scorer

    async def run(self, ctx: RetrievalEvaluationContext) -> None:
        for golden in ctx.goldens:
            chunks = await self._retrieval.retrieve(
                golden.question, ctx.agent_id, ctx.top_k, kb_entry_id=ctx.kb_entry_id
            )
            retrieved_context = [c.text for c in chunks]
            metrics = await self._scorer.score(
                question=golden.question,
                actual_output=golden.expected_output,  # not evaluated — satisfies DeepEval test case schema
                expected_output=golden.expected_output,
                retrieval_context=retrieved_context,
            )
            ctx.question_results.append(
                QuestionResult(
                    question=golden.question,
                    expected_output=golden.expected_output,
                    retrieved_context=retrieved_context,
                    metrics=metrics,
                )
            )
