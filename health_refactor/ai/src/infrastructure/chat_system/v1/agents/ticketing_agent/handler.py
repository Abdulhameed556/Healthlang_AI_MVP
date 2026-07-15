"""Post-close ticketing agent — one combined LLM call per closed session.

Produces ticket worthiness, status, resolution, a summary, the conversation
journey, and (optionally) sentiment. The result feeds a ``TicketDraft`` that the
backend ``create_ticket_for_session`` service persists.
"""
from __future__ import annotations

from typing import Any

from ai.src.domain.chat_system.v1.types import (
    AgentLLMConfig,
    TagOption,
    TicketingAgentInput,
    TicketingAgentResult,
)
from ai.src.domain.llm.types import StructuredSingleTaskAgentResult
from ai.src.infrastructure.chat_system.v1.agents.ticketing_agent.config import (
    AGENT_NAME,
    DEFAULT_CONFIG,
)
from ai.src.infrastructure.chat_system.v1.base.agent import BaseChatSystemAgent

_STATUS_VALUES = ("open", "resolved", "transferred", "failed", "unknown")
_RESOLUTION_VALUES = ("resolved", "transferred", "abandoned", "N/A")
_SENTIMENT_VALUES = ("positive", "neutral", "negative")
_DEFAULT_STATUS = "unknown"
_MAX_TAGS = 10


class TicketingAgent(BaseChatSystemAgent):
    """Analyzes a closed conversation and produces a structured ticket record."""

    def __init__(
        self,
        config: AgentLLMConfig | None = None,
        runner=None,
    ) -> None:
        super().__init__(config or DEFAULT_CONFIG, runner=runner)

    @property
    def name(self) -> str:
        return AGENT_NAME

    async def run(self, input: TicketingAgentInput) -> TicketingAgentResult:
        prompts = self._load_prompts()
        ctx = prompts.PromptContext(
            message_history=input.message_history,
            session_facts=input.session_facts,
            close_reason=input.close_reason,
            enable_sentiment=input.enable_sentiment,
            allowed_tags=input.allowed_tags,
        )
        system_prompt = prompts.build_system_prompt(ctx)
        user_prompt = prompts.build_user_prompt(ctx)

        result = await self._run_structured_with_fallback(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_format=prompts.OUTPUT_FORMAT,
            message_history=input.message_history,
        )

        return self._map_result(
            result,
            enable_sentiment=input.enable_sentiment,
            allowed_tags=input.allowed_tags,
        )

    def _map_result(
        self,
        result: StructuredSingleTaskAgentResult,
        *,
        enable_sentiment: bool,
        allowed_tags: tuple[TagOption, ...],
    ) -> TicketingAgentResult:
        if not result.parse_success:
            return TicketingAgentResult(
                worth_ticket=False,
                status=_DEFAULT_STATUS,
                resolution=None,
                general_summary=None,
                journey=None,
                sentiment=None,
                tags=(),
                raw=result.raw,
                provider=result.provider,
                model=result.model,
                parse_success=False,
            )

        data: dict[str, Any] = result.data or {}
        sentiment = (
            _normalize_optional_choice(data.get("sentiment"), _SENTIMENT_VALUES)
            if enable_sentiment
            else None
        )
        return TicketingAgentResult(
            worth_ticket=_as_bool(data.get("worth_ticket")),
            status=_normalize_choice(
                data.get("status"), _STATUS_VALUES, _DEFAULT_STATUS
            ),
            resolution=_normalize_optional_choice(
                data.get("resolution"), _RESOLUTION_VALUES
            ),
            general_summary=_clean_text(data.get("general_summary")),
            journey=_clean_text(data.get("journey")),
            sentiment=sentiment,
            tags=_normalize_tags(data.get("tags"), allowed_tags),
            raw=result.raw,
            provider=result.provider,
            model=result.model,
            parse_success=True,
        )


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1"}
    return bool(value)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_choice(value: Any, allowed: tuple[str, ...], default: str) -> str:
    text = _clean_text(value)
    if text is None:
        return default
    for option in allowed:
        if text.lower() == option.lower():
            return option
    return default


def _normalize_optional_choice(value: Any, allowed: tuple[str, ...]) -> str | None:
    text = _clean_text(value)
    if text is None or text.lower() == "none":
        return None
    for option in allowed:
        if text.lower() == option.lower():
            return option
    return None


def _normalize_tags(
    value: Any,
    allowed_tags: tuple[TagOption, ...],
) -> tuple[str, ...]:
    """Keep only model-returned tags that match the org's allowed catalog.

    Matching is case-insensitive; the canonical allowed value is preserved.
    Duplicates are removed (order preserved) and the result is capped.
    """
    if not allowed_tags or not isinstance(value, list):
        return ()

    canonical_by_lower = {tag.value.lower(): tag.value for tag in allowed_tags}
    selected: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _clean_text(item)
        if text is None:
            continue
        canonical = canonical_by_lower.get(text.lower())
        if canonical is None or canonical in seen:
            continue
        seen.add(canonical)
        selected.append(canonical)
        if len(selected) >= _MAX_TAGS:
            break
    return tuple(selected)
