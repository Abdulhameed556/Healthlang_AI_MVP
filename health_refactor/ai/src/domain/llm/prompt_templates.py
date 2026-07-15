"""
Central registry of all prompt templates.

Keep prompts here — not scattered across pipeline steps — so that
prompt engineers have one place to review and iterate.
"""

CHAT_SYSTEM_PROMPT = """
You are {agent_name}, an AI assistant for {company_name}.
Language: {language}
Tone: {tone}

## Rules
{rules}

## Scenarios
{scenarios}

## Context from knowledge base
{kb_context}
""".strip()

SIMULATED_USER_PROMPT = """
You are simulating a user interacting with a customer support agent.
Your persona: {persona}
Your goal: {goal}
Respond naturally. When your goal is achieved or you give up, end your turn with [DONE].
""".strip()

JUDGE_PROMPT = """
You are an impartial evaluator scoring a customer service conversation.

Criteria:
{criteria}

Conversation:
{conversation}

Return a JSON object with keys:
  - overall_score (float 0-1)
  - per_criterion (dict mapping criterion name to float 0-1)
  - reasoning (string)
""".strip()

SUMMARISATION_PROMPT = """
Summarise the following customer service conversation in 2-3 sentences.
Then describe the journey (steps taken) in one sentence.
Identify the overall sentiment: positive | neutral | negative.

Conversation:
{conversation}
""".strip()

# Compact system prompts for JSON structured extraction (shape appended by runner).
ORDER_EXTRACTION_SYSTEM = """\
Extract order fields from the user message.
name: company or buyer. products: one object per distinct SKU (id, title, qty).
Only use values from the source."""

TICKET_EXTRACTION_SYSTEM = """\
Triage the user message into ticket fields.
subject: short summary. priority: low|medium|high|critical. tags: string array.
Source text only."""

CLASSIFICATION_EXTRACTION_SYSTEM = """\
Classify the user message.
intent: short snake_case label. confidence: 0-1. entities: type/value pairs."""
