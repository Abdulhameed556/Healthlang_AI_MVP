"""Unit tests: application/chat/session_config.py"""
from ai.src.application.chat.session_config import (
    CONFIG_SOURCE_METADATA_KEY,
    ChatConfigSource,
)


def test_chat_config_source_values() -> None:
    assert ChatConfigSource.DEPLOYED.value == "deployed"
    assert ChatConfigSource.VERSION.value == "version"
    assert ChatConfigSource.DRAFT.value == "draft"


def test_config_source_metadata_key() -> None:
    assert CONFIG_SOURCE_METADATA_KEY == "config_source"
