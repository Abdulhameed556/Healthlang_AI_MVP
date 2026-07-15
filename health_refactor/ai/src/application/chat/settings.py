"""Central chat pipeline settings — edit defaults here.

`ChatPipeline` reads `ChatConfig` per request. This module is the single place
to set deployment defaults. CLI flags and `resolve_chat_config(**overrides)` can
override at runtime.
"""
from __future__ import annotations

import argparse
from dataclasses import replace

from ai.src.domain.chat.config import ChatConfig

# ---------------------------------------------------------------------------
# Edit deployment defaults here
# ---------------------------------------------------------------------------

DEFAULT_AGENT_ID = "235759a2-d469-4dfa-bc59-cd58683499c1"

ENABLE_INPUT_GUARDRAIL = True
ENABLE_OUTPUT_GUARDRAIL = False
ENABLE_SCENARIO_ROUTING = True
USE_TEST_TOOLS = False
USE_SESSION_CACHE = True
ASYNC_SESSION_PERSIST = True

MAX_ORCHESTRATION_LLM_CALLS = 50
MAX_SCENARIOS_PER_TURN = 2
MAX_HISTORY_MESSAGES: int | None = 15

# Knowledge base context is not configured here. Scenario routing returns
# knowledge_base_id + retrieval_query; a retrieval step will inject context into
# the orchestration prompt once that is implemented.

DEFAULT_CHAT_CONFIG = ChatConfig(
    enable_input_guardrail=ENABLE_INPUT_GUARDRAIL,
    enable_output_guardrail=ENABLE_OUTPUT_GUARDRAIL,
    enable_scenario_routing=ENABLE_SCENARIO_ROUTING,
    max_scenarios_per_turn=MAX_SCENARIOS_PER_TURN,
    max_orchestration_llm_calls=MAX_ORCHESTRATION_LLM_CALLS,
    max_history_messages=MAX_HISTORY_MESSAGES,
    use_test_tools=USE_TEST_TOOLS,
    use_session_cache=USE_SESSION_CACHE,
    async_session_persist=ASYNC_SESSION_PERSIST,
)


def resolve_chat_config(
    base: ChatConfig | None = None,
    **overrides: object,
) -> ChatConfig:
    """Return a config with runtime overrides applied to defaults or a base config."""
    if not overrides:
        return base or DEFAULT_CHAT_CONFIG
    cleaned = {key: value for key, value in overrides.items() if value is not None}
    return replace(base or DEFAULT_CHAT_CONFIG, **cleaned)


def add_chat_config_arguments(parser: argparse.ArgumentParser) -> None:
    """Register CLI flags that override :data:`DEFAULT_CHAT_CONFIG`."""
    parser.add_argument("--no-tools", action="store_true", help="Disable API / test tools.")
    parser.add_argument(
        "--no-input-guardrail",
        action="store_true",
        help="Skip input guardrail screening.",
    )
    parser.add_argument(
        "--no-output-guardrail",
        action="store_true",
        help="Skip output guardrail screening.",
    )
    parser.add_argument(
        "--no-scenario-routing",
        action="store_true",
        help="Skip scenario routing before orchestration.",
    )
    parser.add_argument(
        "--max-llm-calls",
        type=int,
        default=MAX_ORCHESTRATION_LLM_CALLS,
        help="Max orchestration LLM turns per message.",
    )
    parser.add_argument(
        "--max-history-messages",
        type=int,
        default=MAX_HISTORY_MESSAGES,
        help="Last N messages from session history passed to the model.",
    )
    parser.add_argument(
        "--use-session-cache",
        action="store_true",
        help="Cache session history in Redis (requires REDIS_URL).",
    )


def chat_config_from_cli_args(
    args: argparse.Namespace,
    *,
    base: ChatConfig | None = None,
) -> ChatConfig:
    """Merge CLI flags onto defaults (or an optional base config)."""
    source = base or DEFAULT_CHAT_CONFIG
    return resolve_chat_config(
        source,
        enable_input_guardrail=source.enable_input_guardrail and not args.no_input_guardrail,
        enable_output_guardrail=source.enable_output_guardrail and not args.no_output_guardrail,
        enable_scenario_routing=source.enable_scenario_routing and not args.no_scenario_routing,
        max_orchestration_llm_calls=args.max_llm_calls,
        max_history_messages=args.max_history_messages,
        use_test_tools=source.use_test_tools and not args.no_tools,
        use_session_cache=source.use_session_cache or args.use_session_cache,
    )
