"""Unit tests: presentation/api/v1/chat/router.py"""
from ai.src.presentation.api.v1.chat.router import router


def test_chat_router_prefix() -> None:
    assert router.prefix == "/chat"


def test_chat_router_includes_session_and_message_routes() -> None:
    paths = {route.path for route in router.routes}
    assert "/chat/sessions" in paths or "/sessions" in paths
    assert "/chat/messages" in paths or "/messages" in paths
