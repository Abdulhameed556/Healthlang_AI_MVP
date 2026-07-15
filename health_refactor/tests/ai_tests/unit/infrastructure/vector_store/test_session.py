"""Unit tests: infrastructure/vector_store/session.py — pgvector stub (no-op since ADR-005)."""
import pytest


@pytest.mark.asyncio
async def test_verify_vector_store_connection_is_no_op() -> None:
    from ai.src.infrastructure.vector_store import session as vector_session

    await vector_session.verify_vector_store_connection()


@pytest.mark.asyncio
async def test_close_vector_store_connection_is_no_op() -> None:
    from ai.src.infrastructure.vector_store import session as vector_session

    await vector_session.close_vector_store_connection()
