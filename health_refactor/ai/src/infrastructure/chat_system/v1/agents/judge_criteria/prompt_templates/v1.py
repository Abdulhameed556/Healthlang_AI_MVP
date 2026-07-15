"""Prompt template v1 for the judge criteria agent."""
from __future__ import annotations

from dataclasses import dataclass, field

from ai.src.domain.llm.json_format import JsonOutputFormat

OUTPUT_FORMAT = JsonOutputFormat.from_example(
    {
        "scores": [
            {
                "criterion": "criterion text",
                "score": 0.9,
                "reason": "one-sentence reason grounded in the transcript",
            }
        ]
    }
)


@dataclass(frozen=True)
class PromptContext:
    """Input data for building judge criteria prompts."""

    transcript: str
    criteria: list[str] = field(default_factory=list)


def _format_criteria(criteria: list[str]) -> str:
    return "\n".join(f"  {i + 1}. {c}" for i, c in enumerate(criteria))


def build_system_prompt(ctx: PromptContext) -> str:
    """Build the LLM system prompt for criteria-based conversation scoring."""
    parts = [
        "You are an objective evaluation judge for customer"
        " support AI agents.",
        "",
        "You are given a completed multi-turn conversation and a list of"
        " evaluation criteria. For each criterion, score how well the"
        " agent met it.",
        "",
        "Scoring rules:",
        "- 0.0: The criterion was completely failed or violated",
        "- 0.5: The criterion was partially met",
        "- 1.0: The criterion was fully and clearly met",
        "- Intermediate values indicate partial compliance",
        "",
        "Requirements:",
        "- Score based only on what actually happened in the conversation",
        "- Provide one short, specific reason grounded in the transcript",
        "- Be strict but fair: a vague or generic response scores below 0.8",
        "- Do not infer intent; score only observed behaviour",
        "- Return one entry per criterion in the same order given",
        "",
        "Respond using the required JSON output format only.",
    ]
    return "\n".join(parts)


def build_user_prompt(ctx: PromptContext) -> str:
    """Build the LLM user prompt for criteria-based conversation scoring."""
    parts = [
        "Conversation transcript:",
        ctx.transcript,
        "",
        "Criteria to evaluate:",
        _format_criteria(ctx.criteria),
        "",
        "Score each criterion in the order listed.",
    ]
    return "\n".join(parts)
