import structlog
from urllib.parse import urlparse

import boto3
from botocore.config import Config

from app.config import settings

logger = structlog.get_logger()


_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        config = None
        if settings.s3_force_path_style:
            config = Config(s3={"addressing_style": "path"})
        _s3_client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            endpoint_url=settings.aws_endpoint_url,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            config=config,
        )
    return _s3_client


def presign_s3_uri(s3_uri: str | None) -> str | None:
    if not s3_uri:
        return None

    parsed = urlparse(s3_uri)
    if parsed.scheme != "s3" or not parsed.netloc:
        logger.warning("invalid_s3_uri", s3_uri=s3_uri)
        return None

    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    if not key:
        logger.warning("invalid_s3_uri_missing_key", s3_uri=s3_uri)
        return None

    try:
        client = get_s3_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=settings.s3_presign_expires_seconds,
        )
    except Exception as exc:
        logger.error("presign_failed", s3_uri=s3_uri, exc_info=exc)
        return None


def presign_row_s3_fields(row: dict, fields: list[str]) -> dict:
    signed = dict(row)
    for field in fields:
        if field in signed:
            signed[field] = presign_s3_uri(signed.get(field))
    return signed


class S3Client:
    """S3 client wrapper for common operations."""

    def __init__(self):
        self.client = get_s3_client()
        self.bucket = settings.s3_bucket

    def object_exists(self, key: str) -> bool:
        """Check if object exists in S3."""
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except self.client.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    def generate_presigned_url(self, key: str, expires_in: int = 900) -> str:
        """Generate presigned URL for S3 object."""
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def upload_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream"):
        """Upload bytes to S3."""
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        logger.info("s3_upload_complete", key=key, size=len(data))

    def upload_json(self, key: str, data: dict):
        """Upload JSON data to S3."""
        import json
        body = json.dumps(data, default=str)
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
        )
        logger.info("s3_json_upload_complete", key=key)
