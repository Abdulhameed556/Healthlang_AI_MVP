"""Pass-through parser for plain text and Markdown files."""


class TextParser:
    def parse(self, content: bytes, file_type: str) -> str:
        return content.decode("utf-8")
