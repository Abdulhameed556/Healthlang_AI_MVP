"""Unit tests: infrastructure/workers/enqueue.py"""
from unittest.mock import patch
from uuid import uuid4

from ai.src.infrastructure.workers.enqueue import (
    enqueue_post_close_pipeline,
    enqueue_session_close_check,
    enqueue_test_task,
)
from ai.src.infrastructure.workers.tasks.health_check import TestTaskInput
from ai.src.infrastructure.workers.tasks.post_close import PostCloseTaskInput
from ai.src.infrastructure.workers.tasks.session_close_check import SessionCloseCheckTaskInput


def test_enqueue_test_task_sends_message_and_returns_payload() -> None:
    with patch(
        "ai.src.infrastructure.workers.tasks.health_check.test_task.send"
    ) as mock_send:
        payload = enqueue_test_task(message="hello worker")

    mock_send.assert_called_once()
    sent_args = mock_send.call_args.args
    assert sent_args[0] == "hello worker"
    # enqueued_at_iso is the second positional arg and is echoed on the payload.
    assert sent_args[1] == payload.enqueued_at_iso

    assert isinstance(payload, TestTaskInput)
    assert payload.message == "hello worker"
    assert payload.enqueued_at_iso


def test_enqueue_post_close_pipeline_sends_session_id_and_returns_payload() -> None:
    session_id = uuid4()

    with patch(
        "ai.src.infrastructure.workers.tasks.post_close.process_post_close.send"
    ) as mock_send:
        payload = enqueue_post_close_pipeline(session_id)

    mock_send.assert_called_once()
    sent_args = mock_send.call_args.args
    assert sent_args[0] == str(session_id)
    # enqueued_at_iso is the second positional arg and is echoed on the payload.
    assert sent_args[1] == payload.enqueued_at_iso

    assert isinstance(payload, PostCloseTaskInput)
    assert payload.session_id == str(session_id)
    assert payload.enqueued_at_iso


def test_enqueue_session_close_check_sends_with_delay_and_returns_payload() -> None:
    session_id = uuid4()

    with patch(
        "ai.src.infrastructure.workers.tasks.session_close_check"
        ".schedule_session_close_check.send_with_options"
    ) as mock_send:
        payload = enqueue_session_close_check(session_id, delay_ms=300000)

    mock_send.assert_called_once()
    call_kwargs = mock_send.call_args.kwargs
    assert call_kwargs["delay"] == 300000
    assert call_kwargs["args"][0] == str(session_id)
    assert call_kwargs["args"][1] == payload.enqueued_at_iso

    assert isinstance(payload, SessionCloseCheckTaskInput)
    assert payload.session_id == str(session_id)
    assert payload.enqueued_at_iso


def test_enqueue_ingest_document_sends_entry_id_and_returns_payload() -> None:
    from ai.src.infrastructure.workers.enqueue import enqueue_ingest_document
    from ai.src.infrastructure.workers.tasks.indexing import IngestDocumentInput

    kb_entry_id = uuid4()

    with patch(
        "ai.src.infrastructure.workers.tasks.indexing.ingest_document.send"
    ) as mock_send:
        payload = enqueue_ingest_document(kb_entry_id)

    mock_send.assert_called_once_with(str(kb_entry_id))
    assert isinstance(payload, IngestDocumentInput)
    assert payload.kb_entry_id == str(kb_entry_id)


def test_enqueue_delete_document_sends_entry_id_and_returns_payload() -> None:
    from ai.src.infrastructure.workers.enqueue import enqueue_delete_document
    from ai.src.infrastructure.workers.tasks.indexing import DeleteDocumentInput

    kb_entry_id = uuid4()

    with patch(
        "ai.src.infrastructure.workers.tasks.indexing.delete_document.send"
    ) as mock_send:
        payload = enqueue_delete_document(kb_entry_id)

    mock_send.assert_called_once_with(str(kb_entry_id))
    assert isinstance(payload, DeleteDocumentInput)
    assert payload.kb_entry_id == str(kb_entry_id)
