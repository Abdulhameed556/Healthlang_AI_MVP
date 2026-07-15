"""Unit tests: ai/src/infrastructure/document_processing/ — parsers, factory, chunker."""
from unittest.mock import MagicMock, patch

import pytest


# ── TextParser ────────────────────────────────────────────────────────────────


def test_text_parser_decodes_utf8_bytes() -> None:
    from ai.src.infrastructure.document_processing.text_parser import TextParser

    result = TextParser().parse(b"hello world", "txt")
    assert result == "hello world"


def test_text_parser_handles_markdown_file_type() -> None:
    from ai.src.infrastructure.document_processing.text_parser import TextParser

    result = TextParser().parse(b"# Heading\n\nParagraph text.", "md")
    assert "Heading" in result
    assert "Paragraph text" in result


def test_text_parser_preserves_whitespace() -> None:
    from ai.src.infrastructure.document_processing.text_parser import TextParser

    content = b"line one\nline two\n"
    assert TextParser().parse(content, "txt") == "line one\nline two\n"


# ── DocxParser ────────────────────────────────────────────────────────────────


def test_docx_parser_extracts_paragraph_text() -> None:
    from ai.src.infrastructure.document_processing.docx_parser import DocxParser

    mock_para = MagicMock()
    mock_para.text = "Leave policy paragraph."
    mock_doc = MagicMock()
    mock_doc.paragraphs = [mock_para]

    _patch = "ai.src.infrastructure.document_processing.docx_parser.Document"
    with patch(_patch, return_value=mock_doc):
        result = DocxParser().parse(b"fake-docx-bytes", "docx")

    assert result == "Leave policy paragraph."


def test_docx_parser_skips_empty_paragraphs() -> None:
    from ai.src.infrastructure.document_processing.docx_parser import DocxParser

    para_a = MagicMock()
    para_a.text = "First paragraph."
    para_empty = MagicMock()
    para_empty.text = "   "
    para_b = MagicMock()
    para_b.text = "Second paragraph."

    mock_doc = MagicMock()
    mock_doc.paragraphs = [para_a, para_empty, para_b]

    _patch = "ai.src.infrastructure.document_processing.docx_parser.Document"
    with patch(_patch, return_value=mock_doc):
        result = DocxParser().parse(b"fake-docx-bytes", "docx")

    assert "First paragraph." in result
    assert "Second paragraph." in result
    assert "   " not in result


# ── ParserFactory ─────────────────────────────────────────────────────────────


def test_parser_factory_returns_docx_parser() -> None:
    from ai.src.infrastructure.document_processing.docx_parser import DocxParser
    from ai.src.infrastructure.document_processing.parser_factory import ParserFactory

    parser = ParserFactory().get_parser("docx")
    assert isinstance(parser, DocxParser)


def test_parser_factory_returns_text_parser_for_txt() -> None:
    from ai.src.infrastructure.document_processing.parser_factory import ParserFactory
    from ai.src.infrastructure.document_processing.text_parser import TextParser

    parser = ParserFactory().get_parser("txt")
    assert isinstance(parser, TextParser)


def test_parser_factory_returns_text_parser_for_md() -> None:
    from ai.src.infrastructure.document_processing.parser_factory import ParserFactory
    from ai.src.infrastructure.document_processing.text_parser import TextParser

    parser = ParserFactory().get_parser("md")
    assert isinstance(parser, TextParser)


def test_parser_factory_is_case_insensitive() -> None:
    from ai.src.infrastructure.document_processing.docx_parser import DocxParser
    from ai.src.infrastructure.document_processing.parser_factory import ParserFactory

    parser = ParserFactory().get_parser("DOCX")
    assert isinstance(parser, DocxParser)


def test_parser_factory_raises_for_unsupported_type() -> None:
    from ai.src.infrastructure.document_processing.parser_factory import ParserFactory

    with pytest.raises(ValueError, match="Unsupported file type"):
        ParserFactory().get_parser("pdf")


# ── TiktokenChunker ───────────────────────────────────────────────────────────


def test_chunker_returns_single_chunk_for_short_text() -> None:
    from ai.src.infrastructure.document_processing.chunker import TiktokenChunker

    chunks = TiktokenChunker().chunk("Hello world.", chunk_size=500, overlap=50)
    assert len(chunks) == 1
    assert "Hello world." in chunks[0]


def test_chunker_returns_empty_list_for_empty_string() -> None:
    from ai.src.infrastructure.document_processing.chunker import TiktokenChunker

    chunks = TiktokenChunker().chunk("", chunk_size=500, overlap=50)
    assert chunks == []


def test_chunker_splits_long_text_into_multiple_chunks() -> None:
    from ai.src.infrastructure.document_processing.chunker import TiktokenChunker

    long_text = "word " * 1200
    chunks = TiktokenChunker().chunk(long_text, chunk_size=500, overlap=50)
    assert len(chunks) > 1


def test_chunker_respects_chunk_size_boundary() -> None:
    from ai.src.infrastructure.document_processing.chunker import TiktokenChunker

    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")
    long_text = "word " * 1200
    chunks = TiktokenChunker().chunk(long_text, chunk_size=100, overlap=10)
    for chunk in chunks:
        assert len(enc.encode(chunk)) <= 100


def test_chunker_overlap_means_adjacent_chunks_share_tokens() -> None:
    from ai.src.infrastructure.document_processing.chunker import TiktokenChunker

    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")
    text = "word " * 300
    chunks = TiktokenChunker().chunk(text, chunk_size=100, overlap=20)
    assert len(chunks) >= 2
    tokens_a = enc.encode(chunks[0])
    tokens_b = enc.encode(chunks[1])
    assert tokens_a[-20:] == tokens_b[:20]
