"""Unit tests: presentation/chat package."""
from ai.src.presentation.api.v1.chat.router import router


def test_presentation_chat_router_is_registered() -> None:
    assert router.prefix == "/chat"
