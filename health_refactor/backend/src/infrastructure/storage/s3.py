"""AWS S3 storage — presigned upload URLs and object existence checks."""
import asyncio

import boto3
from botocore.exceptions import ClientError

from backend.src.core.config import settings

PRESIGNED_URL_EXPIRY = 900  # 15 minutes

_CONTENT_TYPES: dict[str, str] = {
    "docx": (
        "application/vnd.openxmlformats-officedocument"
        ".wordprocessingml.document"
    ),
    "md": "text/markdown",
    "txt": "text/plain",
}


def _get_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def _generate_presigned_upload_url(storage_path: str, file_type: str) -> str:
    client = _get_client()
    content_type = _CONTENT_TYPES.get(file_type, "application/octet-stream")
    return client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.aws_s3_bucket,
            "Key": storage_path,
            "ContentType": content_type,
        },
        ExpiresIn=PRESIGNED_URL_EXPIRY,
    )


def _head_object(storage_path: str) -> bool:
    client = _get_client()
    try:
        client.head_object(Bucket=settings.aws_s3_bucket, Key=storage_path)
        return True
    except ClientError:
        return False


async def generate_presigned_upload_url(
    storage_path: str, file_type: str
) -> str:
    return await asyncio.to_thread(
        _generate_presigned_upload_url, storage_path, file_type
    )


def _put_text_object(storage_path: str, content: str) -> None:
    client = _get_client()
    client.put_object(
        Bucket=settings.aws_s3_bucket,
        Key=storage_path,
        Body=content.encode("utf-8"),
        ContentType="text/plain",
    )


async def upload_text_to_s3(storage_path: str, content: str) -> None:
    await asyncio.to_thread(_put_text_object, storage_path, content)


async def object_exists(storage_path: str) -> bool:
    if storage_path.startswith("http://") or storage_path.startswith("https://"):
        return True
    return await asyncio.to_thread(_head_object, storage_path)


def _delete_object(storage_path: str) -> None:
    client = _get_client()
    client.delete_object(Bucket=settings.aws_s3_bucket, Key=storage_path)


async def delete_s3_object(storage_path: str) -> None:
    if not storage_path or storage_path.startswith("http"):
        return
    await asyncio.to_thread(_delete_object, storage_path)
