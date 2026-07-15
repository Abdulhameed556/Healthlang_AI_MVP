"""Load versioned prompt template modules for chat-system agents."""
from __future__ import annotations

import importlib
from types import ModuleType


def load_prompt_module(agent_name: str, version: str) -> ModuleType:
    """Import ``agents/{agent_name}/prompt_templates/{version}.py``."""
    module_path = (
        f"ai.src.infrastructure.chat_system.v1.agents."
        f"{agent_name}.prompt_templates.{version}"
    )
    return importlib.import_module(module_path)
