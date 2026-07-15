"""FastAPI dependency-injection providers for retrieval."""
from ai.src.application.retrieval.pipeline import RetrievalPipeline
from ai.src.infrastructure.llm.embedder import OpenAIEmbedder
from ai.src.infrastructure.vector_store.pinecone import PineconeVectorStore


def build_retrieval_pipeline() -> RetrievalPipeline:
    return RetrievalPipeline(
        embedder=OpenAIEmbedder(),
        vector_store=PineconeVectorStore(),
    )
