"""Types for single-task LLM agent calls."""
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.messages import ChatMessage


class LLMProviderName(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    GEMINI = "gemini"


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    raw: dict[str, Any] | None = None


@dataclass(frozen=True)
class SingleTaskAgentRequest:
    """One-shot agent call: system + optional history + user prompt."""

    system_prompt: str
    prompt: str
    provider: str
    model: str
    message_history: tuple[ChatMessage, ...] = ()
    temperature: float | None = None
    max_tokens: int | None = None
    max_retries: int = 2
    stream: bool = False
    stream_usage: bool = False


@dataclass(frozen=True)
class SingleTaskAgentResult:
    content: str
    provider: str
    model: str
    usage: TokenUsage | None = None


@dataclass(frozen=True)
class VisionAgentRequest:
    """One-shot vision call: system prompt, optional user text, and image URL(s)."""

    system_prompt: str
    prompt: str
    image_urls: tuple[str, ...]
    provider: str
    model: str
    temperature: float | None = None
    max_tokens: int | None = None
    max_retries: int = 2


@dataclass(frozen=True)
class StructuredSingleTaskAgentRequest:
    """Single-task call with JSON-in-<json> structured output."""

    system_prompt: str
    prompt: str
    provider: str
    model: str
    output_format: JsonOutputFormat
    message_history: tuple[ChatMessage, ...] = ()
    temperature: float | None = None
    max_tokens: int | None = None
    max_retries: int = 2
    stream_usage: bool = False


@dataclass(frozen=True)
class StructuredSingleTaskAgentResult:
    data: dict[str, Any]
    raw: str
    provider: str
    model: str
    usage: TokenUsage | None = None
    parse_success: bool = False
    parse_errors: tuple[str, ...] = ()
