"""Unit tests: infrastructure/workers/_base.py"""
import logging

from ai.src.infrastructure.workers._base import (
    log_task_end,
    log_task_skipped,
    log_task_start,
    run_async,
)


def test_run_async_executes_coroutine_and_returns_value() -> None:
    async def _coro() -> int:
        return 42

    assert run_async(_coro()) == 42


def test_log_helpers_emit_under_ai_workers_logger(caplog) -> None:
    with caplog.at_level(logging.INFO, logger="ai.workers"):
        log_task_start("test_task", {"message": "hi"})
        log_task_end("test_task", {"outcome": "processed"})
        log_task_skipped("test_task", "not_due", session_id="abc")

    messages = " ".join(record.getMessage() for record in caplog.records)
    assert "worker_task_start" in messages
    assert "worker_task_end" in messages
    assert "worker_task_skipped" in messages
    assert "not_due" in messages
