"""Compile the chat orchestration LangGraph (LLM + optional tools loop)."""
from collections.abc import Sequence

from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ai.src.domain.chat_system.v1.types import AgentLLMConfig
from ai.src.infrastructure.chat_system.v1.orchestration.config import DEFAULT_CONFIG
from ai.src.infrastructure.chat_system.v1.orchestration.edges import create_should_continue
from ai.src.infrastructure.chat_system.v1.orchestration.model import build_chat_model
from ai.src.infrastructure.chat_system.v1.orchestration.nodes.llm_node import create_llm_node
from ai.src.infrastructure.chat_system.v1.orchestration.nodes.tool_node import create_tool_node
from ai.src.infrastructure.chat_system.v1.orchestration.state import ChatGraphState, MAX_LLM_CALLS


def compile_chat_graph(
    config: AgentLLMConfig = DEFAULT_CONFIG,
    *,
    tools: Sequence[BaseTool] = (),
    max_llm_calls: int = MAX_LLM_CALLS,
) -> CompiledStateGraph:
    """Build and compile the chat graph: llm → (tools → llm)* → END when tools are set."""
    llm = build_chat_model(config)
    fallback_llm = None
    fallback_model: str | None = None
    if config.fallback_provider:
        fallback_model = config.fallback_model or config.model
        fallback_llm = build_chat_model(
            config,
            provider=config.fallback_provider,
            model=fallback_model,
        )

    tool_list = list(tools)
    route = create_should_continue(max_llm_calls=max_llm_calls)
    if tool_list:
        llm = llm.bind_tools(tool_list)
        if fallback_llm is not None:
            fallback_llm = fallback_llm.bind_tools(tool_list)

    graph = StateGraph(ChatGraphState)
    graph.add_node(
        "llm",
        create_llm_node(
            llm,
            fallback_llm=fallback_llm,
            primary_provider=config.provider,
            primary_model=config.model,
            fallback_provider=config.fallback_provider,
            fallback_model=fallback_model,
        ),
    )

    if tool_list:
        graph.add_node("tools", create_tool_node(tool_list))
        graph.add_edge(START, "llm")
        graph.add_conditional_edges("llm", route, {"tools": "tools", END: END})
        graph.add_edge("tools", "llm")
    else:
        graph.add_edge(START, "llm")
        graph.add_edge("llm", END)

    return graph.compile()
