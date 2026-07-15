"""Unit tests: ai/src/infrastructure/chat_system package imports."""
import ai.src.domain.chat_system
import ai.src.domain.chat_system.v1
import ai.src.infrastructure.chat_system
import ai.src.infrastructure.chat_system.v1
import ai.src.infrastructure.chat_system.v1.base


def test_chat_system_packages_import() -> None:
    assert ai.src.infrastructure.chat_system.v1 is not None
    assert ai.src.domain.chat_system.v1 is not None
