"""Load versioned prompt template modules for chat orchestration."""
from __future__ import annotations

import importlib
from types import ModuleType

from ai.src.infrastructure.chat_system.v1.orchestration.config import DEFAULT_CONFIG


def load_prompt_module(version: str | None = None) -> ModuleType:
    """Import ``orchestration/prompt_templates/{version}.py``."""
    resolved = version or DEFAULT_CONFIG.prompt_version
    module_path = (
        f"ai.src.infrastructure.chat_system.v1.orchestration."
        f"prompt_templates.{resolved}"
    )
    return importlib.import_module(module_path)
