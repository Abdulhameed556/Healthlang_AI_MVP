"""Pipeline step: download the raw file bytes from S3."""
from ai.src.application.indexing.context import IndexingContext
from ai.src.infrastructure.storage.s3 import download_file


class FetchDocumentStep:
    async def run(self, ctx: IndexingContext) -> None:
        ctx.raw_bytes = await download_file(ctx.storage_path)
