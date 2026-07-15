"""Return the right parser for a given file_type."""
from ai.src.infrastructure.document_processing.docx_parser import DocxParser
from ai.src.infrastructure.document_processing.text_parser import TextParser


class ParserFactory:
    _TEXT_TYPES = {"txt", "md"}

    def get_parser(self, file_type: str):
        ft = file_type.lower()
        if ft == "docx":
            return DocxParser()
        if ft in self._TEXT_TYPES:
            return TextParser()
        raise ValueError(f"Unsupported file type: {file_type!r}")
