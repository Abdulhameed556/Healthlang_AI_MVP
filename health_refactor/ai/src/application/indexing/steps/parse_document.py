"""Pipeline step: parse raw bytes into plain text using the correct parser."""
from ai.src.application.indexing.context import IndexingContext
from ai.src.infrastructure.document_processing.parser_factory import ParserFactory


class ParseDocumentStep:
    def __init__(self, parser_factory: ParserFactory) -> None:
        self._factory = parser_factory

    async def run(self, ctx: IndexingContext) -> None:
        parser = self._factory.get_parser(ctx.file_type)
        ctx.text = parser.parse(ctx.raw_bytes, ctx.file_type)
