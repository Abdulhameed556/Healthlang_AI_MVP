"""Unit tests: presentation/api/v1/chat/endpoints/message.py"""
from ai.src.presentation.api.v1.chat.endpoints.message import router


def test_message_endpoint_registers_post_route() -> None:
    paths = [route.path for route in router.routes]
    assert "/messages" in paths
