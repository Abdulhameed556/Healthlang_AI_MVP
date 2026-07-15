"""Unit tests: presentation/api/v1/chat/endpoints/session.py"""
from ai.src.presentation.api.v1.chat.endpoints.session import router


def test_session_endpoint_registers_post_route() -> None:
    paths = [route.path for route in router.routes]
    assert "/sessions" in paths
