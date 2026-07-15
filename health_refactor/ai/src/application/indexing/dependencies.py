"""Wires all concrete dependencies into IndexingPipeline."""
from ai.src.application.indexing.pipeline import IndexingPipeline
from ai.src.infrastructure.document_processing.chunker import TiktokenChunker
from ai.src.infrastructure.document_processing.parser_factory import ParserFactory
from ai.src.infrastructure.llm.embedder import OpenAIEmbedder
from ai.src.infrastructure.vector_store.pinecone import PineconeVectorStore
from backend.src.infrastructure.database.session import async_session_factory


def build_indexing_pipeline() -> IndexingPipeline:
    return IndexingPipeline(
        session_factory=async_session_factory,
        embedder=OpenAIEmbedder(),
        vector_store=PineconeVectorStore(),
        parser_factory=ParserFactory(),
        chunker=TiktokenChunker(),
    )
