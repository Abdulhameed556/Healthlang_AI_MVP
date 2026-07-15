"""Structured logging for chat pipeline steps."""
from __future__ import annotations

import logging
from typing import Any

from backend.src.core.logging import green

logger = logging.getLogger("ai.chat.pipeline")

_RED = "\033[1;31m"
_RESET = "\033[0m"


def _render_fields(**fields: Any) -> str:
    parts: list[str] = []
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, bool):
            text = "true" if value else "false"
        elif isinstance(value, (list, tuple)):
            text = ",".join(str(item) for item in value)
        else:
            text = str(value).replace("\n", " ").strip()
        if not text:
            continue
        parts.append(f"{key}={text}")
    return " ".join(parts)


def log_pipeline_step(
    session_id: str,
    step: str,
    *,
    duration_ms: float | None = None,
    level: str = "info",
    **fields: Any,
) -> None:
    message = _render_fields(
        session_id=session_id,
        step=step,
        duration_ms=f"{duration_ms:.1f}" if duration_ms is not None else None,
        **fields,
    )
    if level == "warning":
        logger.warning("chat_pipeline %s", message)
    elif level == "error":
        logger.error("chat_pipeline %s", message)
    else:
        logger.info("chat_pipeline %s", message)


def log_pipeline_timing_summary(session_id: str, timing: dict[str, float]) -> None:
    """One green line summarizing where the pipeline spent time on this turn."""

    def _s(key: str) -> float:
        return timing.get(key, 0.0) / 1000.0

    logger.info(
        green(
            "chat_pipeline_timing session=%s total=%.2fs | session_load=%.2fs "
            "runtime_load=%.2fs input_guardrail=%.2fs scenario_routing=%.2fs "
            "orchestration=%.2fs output_guardrail=%.2fs persist_turn=%.2fs"
        ),
        session_id,
        _s("total"),
        _s("session_load"),
        _s("runtime_load"),
        _s("input_guardrail"),
        _s("scenario_routing"),
        _s("orchestration"),
        _s("output_guardrail"),
        _s("persist_turn"),
    )


def log_session_facts(
    session_id: str,
    *,
    previous: dict[str, Any],
    delta: dict[str, Any],
    merged: dict[str, Any],
) -> None:
    """Log session facts for a turn in red so they stand out in the console.

    Renders the prior facts, this turn's delta, and the merged result, making it
    easy to trace what the agent has learned and stored across the conversation.
    """
    message = _render_fields(
        session_id=session_id,
        step="session_facts",
        previous=previous or {},
        delta=delta or {},
        merged=merged or {},
    )
    logger.info("%schat_pipeline %s%s", _RED, message, _RESET)
