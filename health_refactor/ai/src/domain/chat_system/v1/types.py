"""Shared types for chat system v1 agents."""
from dataclasses import dataclass
from enum import StrEnum

from ai.src.domain.llm.messages import ChatMessage
from backend.src.domain.agents.brand_personalization import (
    BrandConfig,
    PersonalizationConfig,
)


class PromptInjectionCategory(StrEnum):
    """Known prompt-injection attack categories."""

    IGNORE_OVERRIDE = "ignore_override"
    PERSONA_HIJACK = "persona_hijack"
    DELIMITER_SMUGGLING = "delimiter_smuggling"
    INDIRECT_INJECTION = "indirect_injection"
    EXFILTRATION = "exfiltration"
    OBFUSCATION = "obfuscation"
    MULTI_TURN_ESCALATION = "multi_turn_escalation"
    CUSTOM_RULE = "custom_rule"
    NONE = "none"


@dataclass(frozen=True)
class AgentLLMConfig:
    """LLM routing for a chat-system agent."""

    provider: str
    model: str
    prompt_version: str
    fallback_provider: str | None = None
    fallback_model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    max_retries: int = 2


@dataclass(frozen=True)
class GuardrailInputScreenerInput:
    """Input to the guardrail input screener."""

    user_query: str
    message_history: tuple[ChatMessage, ...] = ()
    rules: tuple[str, ...] = ()
    sentinel: str = "===SYS_BOUNDARY==="


@dataclass(frozen=True)
class GuardrailInputScreenerResult:
    """Structured screening decision for a user message."""

    blocked: bool
    blocked_reason: str | None
    attack_category: PromptInjectionCategory | None
    raw: str
    provider: str
    model: str
    parse_success: bool


class OutputViolationCategory(StrEnum):
    """Known agent-output policy violations."""

    SYSTEM_PROMPT_LEAK = "system_prompt_leak"
    HARMFUL_CONTENT = "harmful_content"
    PII_EXPOSURE = "pii_exposure"
    OFF_BRAND = "off_brand"
    POLICY_VIOLATION = "policy_violation"
    CUSTOM_RULE = "custom_rule"
    NONE = "none"


class OutputDeliveryAction(StrEnum):
    """How the screened assistant message should be delivered."""

    PASS = "pass"
    REFORMAT = "reformat"
    BLOCK = "block"


@dataclass(frozen=True)
class GuardrailOutputScreenerInput:
    """Input to the guardrail output screener."""

    agent_output: str
    user_query: str = ""
    message_history: tuple[ChatMessage, ...] = ()
    rules: tuple[str, ...] = ()
    tools_used: tuple[str, ...] = ()
    agent_name: str = ""
    brand_config: BrandConfig | None = None
    personalization_config: PersonalizationConfig | None = None
    sentinel: str = "===SYS_BOUNDARY==="


@dataclass(frozen=True)
class GuardrailOutputScreenerResult:
    """Structured screening decision for an agent response."""

    action: OutputDeliveryAction
    blocked: bool
    safe_message: str | None
    blocked_reason: str | None
    violation_category: OutputViolationCategory | None
    raw: str
    provider: str
    model: str
    parse_success: bool


@dataclass(frozen=True)
class ScenarioContextOption:
    """Selectable item with id, name, and description."""

    id: str
    name: str
    description: str


@dataclass(frozen=True)
class TagOption:
    """An organization classification tag offered to the ticketing agent.

    ``value`` is the snake_case label the agent may assign to a ticket;
    ``description`` is optional guidance on when the tag applies.
    """

    value: str
    description: str = ""


@dataclass(frozen=True)
class CurrentScenario:
    """Active scenario context for the current conversation turn."""

    title: str
    description: str


@dataclass(frozen=True)
class CurrentKnowledgeBase:
    """Active knowledge base context for the current conversation turn."""

    title: str
    description: str


@dataclass(frozen=True)
class ScenarioAgentInput:
    """Input to the scenario routing agent.

    Routing catalog (scenarios and knowledge bases) is loaded from the
    deployed agent snapshot using agent_id.
    """

    agent_id: str
    user_query: str
    message_history: tuple[ChatMessage, ...] = ()
    current_scenario: CurrentScenario | None = None
    current_knowledge_base: CurrentKnowledgeBase | None = None
    max_scenarios_per_turn: int = 1


@dataclass(frozen=True)
class ScenarioAgentResult:
    """Structured routing decision for a user turn.

    Pipeline should persist scenario_ids and knowledge_base_id per turn.
    Agent rules are always loaded into the orchestrator from the deployed snapshot;
    rule_ids is retained for metadata compatibility and is always empty.
    When knowledge_base_id is set, use retrieval_query for vector search on policy/docs KB.
    Use experience_queries (1-2 items) to search the past-resolution experience store.
    """

    scenario_ids: tuple[str, ...]
    knowledge_base_id: str | None
    rule_ids: tuple[str, ...]
    retrieval_query: str | None
    experience_queries: tuple[str, ...]
    reason: str
    raw: str
    provider: str
    model: str
    parse_success: bool


@dataclass(frozen=True)
class ImageReaderAgentInput:
    """Input to the image reader agent (vision preprocessing for inbound attachments)."""

    image_urls: tuple[str, ...]
    caption: str = ""


@dataclass(frozen=True)
class ImageReaderAgentResult:
    """Plain-text description extracted from customer image attachment(s)."""

    description: str
    raw: str
    provider: str
    model: str
    success: bool
    error: str | None = None


@dataclass(frozen=True)
class TicketingAgentInput:
    """Input to the post-close ticketing agent (one combined LLM call).

    The full conversation is passed as ``message_history`` so the model reads the
    actual transcript; ``session_facts`` are durable facts gathered during the chat.
    ``enable_sentiment`` is honored only when the agent is configured for it.
    ``allowed_tags`` is the organization's current tag catalog; the agent may only
    assign tags from this list (or none).
    """

    message_history: tuple[ChatMessage, ...] = ()
    session_facts: dict[str, str] | None = None
    close_reason: str | None = None
    enable_sentiment: bool = False
    allowed_tags: tuple[TagOption, ...] = ()


@dataclass(frozen=True)
class TicketingAgentResult:
    """Combined ticket-worthiness + summary + sentiment decision for a closed session.

    ``status`` is one of open/resolved/transferred/failed/unknown; ``resolution`` is
    one of resolved/transferred/abandoned/N/A or None; ``sentiment`` is
    positive/neutral/negative and is only populated when sentiment analysis is enabled.
    ``tags`` is the subset of the organization's allowed tags the agent assigned to
    this conversation (validated against ``TicketingAgentInput.allowed_tags``).
    """

    worth_ticket: bool
    status: str
    resolution: str | None
    general_summary: str | None
    journey: str | None
    sentiment: str | None
    tags: tuple[str, ...]
    raw: str
    provider: str
    model: str
    parse_success: bool


class ConversationSessionState(StrEnum):
    """Lifecycle state for a customer support session (tracked per conversation)."""

    IN_PROGRESS = "in_progress"
    WAITING_ON_CUSTOMER = "waiting_on_customer"
    PENDING_CLOSE = "pending_close"
    END_CONVERSATION = "end_conversation"
    TRANSFER_TO_LIVE_SUPPORT = "transfer_to_live_support"


class TicketAction(StrEnum):
    """Whether the orchestrator wants a ticket opened for the issue just handled.

    Used by external channels (e.g. Freshchat) where one conversation can hold
    several issues, so the model signals per turn when an issue is ticket-worthy.
    The default chat flow never asks for this, so it stays ``none``.
    """

    NONE = "none"
    CREATE_TICKET = "create_ticket"


@dataclass(frozen=True)
class OrchestrationTurnResult:
    """Structured final reply from the main chat orchestration agent."""

    message: str
    conversation_state: ConversationSessionState
    session_facts: dict[str, str]
    raw: str
    parse_success: bool
    ticket_action: TicketAction = TicketAction.NONE
    ticket_reason: str | None = None
    # Whether the customer's issue was actually resolved on this turn. Only
    # external channels (Freshchat) ask the model for this; null when not set.
    issue_resolved: bool | None = None
