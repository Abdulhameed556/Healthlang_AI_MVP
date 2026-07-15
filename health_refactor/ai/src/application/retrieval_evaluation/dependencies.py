"""Wires concrete dependencies into the retrieval-evaluation pipeline."""
from ai.src.application.retrieval.dependencies import build_retrieval_pipeline
from ai.src.application.retrieval_evaluation.pipeline import RetrievalEvaluationPipeline
from ai.src.application.retrieval_evaluation.steps.load_source_chunks import (
    LoadSourceChunksStep,
)
from ai.src.application.retrieval_evaluation.steps.run_test_cases import RunTestCasesStep
from ai.src.application.retrieval_evaluation.steps.synthesize_testset import (
    SynthesizeTestsetStep,
)
from ai.src.infrastructure.document_processing.chunker import TiktokenChunker
from ai.src.infrastructure.document_processing.parser_factory import ParserFactory
from ai.src.infrastructure.retrieval_evaluation.run_store import get_run_store
from ai.src.infrastructure.retrieval_evaluation.scorer import DeepEvalScorer
from ai.src.infrastructure.retrieval_evaluation.synthesizer import DeepEvalSynthesizer
from backend.src.infrastructure.database.session import async_session_factory


def build_retrieval_evaluation_pipeline() -> RetrievalEvaluationPipeline:
    return RetrievalEvaluationPipeline(
        steps=[
            LoadSourceChunksStep(
                async_session_factory, ParserFactory(), TiktokenChunker()
            ),
            SynthesizeTestsetStep(DeepEvalSynthesizer()),
            RunTestCasesStep(
                build_retrieval_pipeline(),
                DeepEvalScorer(),
            ),
        ],
        run_store=get_run_store(),
    )
