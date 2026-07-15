"""Structured logging for chat-system LLM calls."""
from __future__ import annotations

import logging

from ai.src.domain.llm.types import (
    SingleTaskAgentResult,
    StructuredSingleTaskAgentResult,
    TokenUsage,
)

logger = logging.getLogger("ai.chat.llm")


def preview_output(text: str | None, *, max_len: int = 160) -> str:
    if not text:
        return ""
    collapsed = " ".join(text.split())
    if len(collapsed) <= max_len:
        return collapsed
    return f"{collapsed[: max_len - 3]}..."


def format_token_usage(usage: TokenUsage | None) -> str:
    if usage is None:
        return "unknown"
    parts: list[str] = []
    if usage.input_tokens is not None:
        parts.append(f"in={usage.input_tokens}")
    if usage.output_tokens is not None:
        parts.append(f"out={usage.output_tokens}")
    if usage.total_tokens is not None:
        parts.append(f"total={usage.total_tokens}")
    return ",".join(parts) if parts else "unknown"


def _log_fields(**fields: object) -> str:
    rendered: list[str] = []
    for key, value in fields.items():
        if value is None:
            continue
        text = str(value).replace("\n", " ").strip()
        if not text:
            continue
        rendered.append(f"{key}={text}")
    return " ".join(rendered)


def log_llm_call(
    *,
    component: str,
    attempt: str,
    provider: str,
    model: str,
    outcome: str,
    duration_ms: float,
    usage: TokenUsage | None = None,
    error: str | None = None,
    output_preview: str | None = None,
    parse_success: bool | None = None,
    tool_calls: int | None = None,
    llm_call_number: int | None = None,
) -> None:
    """Emit one line per LLM attempt (primary, fallback, orchestration turn)."""
    fields = _log_fields(
        component=component,
        attempt=attempt,
        provider=provider,
        model=model,
        outcome=outcome,
        duration_ms=f"{duration_ms:.1f}",
        tokens=format_token_usage(usage),
        error=preview_output(error, max_len=200) if error else None,
        output=preview_output(output_preview) if output_preview else None,
        parse_success=parse_success,
        tool_calls=tool_calls,
        llm_call_number=llm_call_number,
    )
    if outcome == "failed":
        logger.warning("chat_llm %s", fields)
    else:
        logger.info("chat_llm %s", fields)


def result_output_preview(
    result: SingleTaskAgentResult | StructuredSingleTaskAgentResult,
) -> str:
    if isinstance(result, StructuredSingleTaskAgentResult):
        return result.raw
    return result.content


def resolve_langchain_model_name(llm: object) -> str:
    for attr in ("model_name", "model", "model_id"):
        value = getattr(llm, attr, None)
        if isinstance(value, str) and value:
            return value
    return "unknown"
