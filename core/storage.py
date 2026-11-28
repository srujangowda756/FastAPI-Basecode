import uuid

import boto3
from botocore.config import Config
from fastapi.concurrency import run_in_threadpool

from core.config import settings

_client = boto3.client(
    "s3",
    endpoint_url=settings.S3_ENDPOINT,
    aws_access_key_id=settings.S3_ACCESS_KEY,
    aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
    region_name=settings.S3_REGION,
    config=Config(signature_version="s3v4"),
)


def profile_keys(photo_id: uuid.UUID) -> tuple[str, str]:
    return f"profiles/{photo_id}.webp", f"profiles/{photo_id}_thumb.webp"


def _put(key: str, data: bytes) -> None:
    _client.put_object(
        Bucket=settings.S3_BUCKET, Key=key, Body=data, ContentType="image/webp"
    )


def _delete(keys: list[str]) -> None:
    for key in keys:
        _client.delete_object(Bucket=settings.S3_BUCKET, Key=key)


async def upload_bytes(key: str, data: bytes) -> None:
    await run_in_threadpool(_put, key, data)


async def delete_keys(keys: list[str]) -> None:
    await run_in_threadpool(_delete, keys)


def signed_url(key: str) -> str:
    # local computation, no network call
    return _client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.S3_BUCKET, "Key": key},
        ExpiresIn=settings.SIGNED_URL_EXPIRE_SECONDS,
    )

