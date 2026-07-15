"""Config source for builder test chat sessions."""
from enum import StrEnum

CONFIG_SOURCE_METADATA_KEY = "config_source"


class ChatConfigSource(StrEnum):
    """Which agent configuration snapshot to run in a chat session."""

    DEPLOYED = "deployed"
    VERSION = "version"
    DRAFT = "draft"
