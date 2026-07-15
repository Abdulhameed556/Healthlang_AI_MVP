"""Prompt template v1 for the conversation generator agent."""
from __future__ import annotations

from dataclasses import dataclass, field

from ai.src.domain.llm.json_format import JsonOutputFormat

OUTPUT_FORMAT = JsonOutputFormat.from_example(
    {
        "conversations": [
            {
                "persona": "frustrated_customer",
                "turns": [
                    {
                        "user": "customer message text",
                        "agent_expected": "expected agent reply",
                    }
                ],
            }
        ]
    }
)

PERSONA_DESCRIPTIONS: dict[str, str] = {
    "frustrated_customer": (
        "A customer who has been waiting too long or had a bad experience. "
        "They are impatient, direct, and use short sentences "
        "expressing frustration."
    ),
    "confused_first_timer": (
        "A first-time user who doesn't understand how the product works. "
        "They ask basic questions, often repeat themselves, "
        "and need step-by-step guidance."
    ),
    "polite_but_persistent": (
        "A courteous customer who keeps pushing for more information. "
        "They are respectful but follow up with detailed follow-on questions."
    ),
    "skeptical_user": (
        "A customer who questions everything — fees, policies, timelines. "
        "They want proof, specifics, and don't accept vague answers."
    ),
    "calm_detailed": (
        "A methodical customer who explains their situation thoroughly and "
        "asks clear, well-structured questions."
    ),
}


@dataclass(frozen=True)
class PromptContext:
    """Input data for building conversation generator prompts."""

    agent_name: str
    scenario_name: str
    scenario_description: str
    scenario_prompt: str
    persona_1: str
    persona_2: str
    knowledge_bases: list[dict] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    conversation_rounds: int = 5
    agent_variables: dict = field(default_factory=dict)


def _format_knowledge_bases(kbs: list[dict]) -> str:
    if not kbs:
        return "  (none configured)"
    return "\n".join(
        f"  - {kb['name']}: {kb['description']}" for kb in kbs
    )


def _format_rules(rules: list[str]) -> str:
    if not rules:
        return "  (none configured)"
    return "\n".join(f"  - {r}" for r in rules)


def _format_agent_variables(variables: dict) -> str:
    """Format agent_variables key/value pairs for the system prompt."""
    if not variables:
        return "  (none provided)"
    return "\n".join(f"  {k}: {v}" for k, v in variables.items())


def _persona_block(persona: str) -> str:
    desc = PERSONA_DESCRIPTIONS.get(persona, persona)
    return f"  {persona}: {desc}"


def build_system_prompt(ctx: PromptContext) -> str:
    """Build the LLM system prompt for synthetic conversation generation."""
    guidance = ctx.scenario_prompt or "(standard handling)"
    rounds_rule = (
        f"- Each conversation must have exactly {ctx.conversation_rounds}"
        " turns."
    )
    agent_expected_rule = (
        "- agent_expected: a helpful, accurate response the agent SHOULD"
        " give, following rules and referencing KB info where relevant."
        " Do NOT expose sensitive data (PINs, full card numbers,"
        " passwords). Keep agent replies concise (1–3 sentences)."
    )

    parts = [
        "You are a conversation simulator for testing"
        " a customer support AI agent.",
        "",
        "Your task: generate 2 realistic multi-turn conversations between"
        " a customer and the support agent for the given scenario."
        " Use the two specified customer personas.",
        "",
        f"Agent name: {ctx.agent_name}",
        "",
        "Scenario being tested:",
        f"  Name: {ctx.scenario_name}",
        f"  Description: {ctx.scenario_description}",
        f"  Agent guidance: {guidance}",
        "",
        "Knowledge bases the agent can reference:",
        _format_knowledge_bases(ctx.knowledge_bases),
        "",
        "Rules the agent must follow:",
        _format_rules(ctx.rules),
    ]

    if ctx.agent_variables:
        parts += [
            "",
            "Customer context for this session:",
            _format_agent_variables(ctx.agent_variables),
            "(Reference these facts naturally in the customer's messages"
            " — do not announce them directly.)",
        ]

    parts += [
        "",
        "Personas to simulate:",
        _persona_block(ctx.persona_1),
        _persona_block(ctx.persona_2),
        "",
        "Requirements:",
        rounds_rule,
        "- user: realistic customer message matching the persona.",
        agent_expected_rule,
        "- Conversations must stay on-topic for the scenario.",
        "- Vary phrasing — do not repeat the same words across conversations.",
        "",
        "Respond using the required JSON output format only.",
    ]

    return "\n".join(parts)


def build_user_prompt(ctx: PromptContext) -> str:
    """Build the LLM user prompt for synthetic conversation generation."""
    return (
        f"Generate 2 conversations for scenario '{ctx.scenario_name}' "
        f"using personas: {ctx.persona_1} and {ctx.persona_2}."
    )
