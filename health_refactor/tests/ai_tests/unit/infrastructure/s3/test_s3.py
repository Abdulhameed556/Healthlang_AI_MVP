"""Unit tests: ai/src/infrastructure/storage/s3.py — download_file."""
from unittest.mock import MagicMock

import pytest


def _make_s3_client(body: bytes = b"file bytes") -> MagicMock:
    mock_body = MagicMock()
    mock_body.read.return_value = body
    client = MagicMock()
    client.get_object.return_value = {"Body": mock_body}
    return client


@pytest.mark.asyncio
async def test_download_file_calls_get_object(monkeypatch) -> None:
    import ai.src.infrastructure.storage.s3 as s3_module

    mock_client = _make_s3_client()
    monkeypatch.setattr(s3_module, "_get_client", lambda: mock_client)

    await s3_module.download_file("knowledge-bases/kb-1/entry-1.docx")

    mock_client.get_object.assert_called_once()


@pytest.mark.asyncio
async def test_download_file_returns_raw_bytes(monkeypatch) -> None:
    import ai.src.infrastructure.storage.s3 as s3_module

    expected = b"raw document bytes"
    mock_client = _make_s3_client(body=expected)
    monkeypatch.setattr(s3_module, "_get_client", lambda: mock_client)

    result = await s3_module.download_file("knowledge-bases/kb-1/entry-1.docx")

    assert result == expected


@pytest.mark.asyncio
async def test_download_file_passes_correct_bucket_and_key(monkeypatch) -> None:
    import ai.src.infrastructure.storage.s3 as s3_module

    mock_client = _make_s3_client()
    monkeypatch.setattr(s3_module, "_get_client", lambda: mock_client)
    monkeypatch.setattr(s3_module.settings, "aws_s3_bucket", "test-bucket")

    storage_path = "knowledge-bases/kb-1/entry-1.docx"
    await s3_module.download_file(storage_path)

    mock_client.get_object.assert_called_once_with(Bucket="test-bucket", Key=storage_path)


@pytest.mark.asyncio
async def test_download_file_fetches_http_url(respx_mock) -> None:
    import httpx
    import ai.src.infrastructure.storage.s3 as s3_module

    url = "https://example.com/document.txt"
    respx_mock.get(url).mock(return_value=httpx.Response(200, content=b"http content"))

    result = await s3_module.download_file(url)

    assert result == b"http content"


@pytest.mark.asyncio
async def test_download_file_fetches_https_url(respx_mock) -> None:
    import httpx
    import ai.src.infrastructure.storage.s3 as s3_module

    url = "http://example.com/document.md"
    respx_mock.get(url).mock(return_value=httpx.Response(200, content=b"plain http"))

    result = await s3_module.download_file(url)

    assert result == b"plain http"


def test_get_client_builds_boto3_s3_client(monkeypatch) -> None:
    from unittest.mock import MagicMock, patch
    import ai.src.infrastructure.storage.s3 as s3_module

    monkeypatch.setattr(s3_module.settings, "aws_access_key_id", "AKIATEST")
    monkeypatch.setattr(s3_module.settings, "aws_secret_access_key", "secret")

    mock_client = MagicMock()
    with patch("boto3.client", return_value=mock_client) as mock_boto:
        result = s3_module._get_client()

    mock_boto.assert_called_once_with(
        "s3",
        aws_access_key_id="AKIATEST",
        aws_secret_access_key="secret",
    )
    assert result is mock_client
