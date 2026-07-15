"""Download documents from S3 or public HTTP URLs for the indexing pipeline."""
import asyncio

import boto3
import httpx

from ai.src.core.config import settings


def _get_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def _download_from_s3(storage_path: str) -> bytes:
    client = _get_client()
    response = client.get_object(Bucket=settings.aws_s3_bucket, Key=storage_path)
    return response["Body"].read()


async def download_file(storage_path: str) -> bytes:
    """Download a file from S3 or a public HTTP URL and return its raw bytes."""
    if storage_path.startswith("http://") or storage_path.startswith("https://"):
        async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
            response = await client.get(storage_path)
            response.raise_for_status()
            return response.content
    return await asyncio.to_thread(_download_from_s3, storage_path)
