"""Unit tests: image_reader package exports."""
from ai.src.infrastructure.chat_system.v1.agents import image_reader


def test_image_reader_package_exports() -> None:
    assert image_reader.AGENT_NAME == "image_reader"
    assert image_reader.DEFAULT_CONFIG is not None
    assert image_reader.ImageReaderAgent is not None
    assert "ImageReaderAgent" in image_reader.__all__
