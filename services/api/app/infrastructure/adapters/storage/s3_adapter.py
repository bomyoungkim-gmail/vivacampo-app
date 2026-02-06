"""S3 adapter implementing IObjectStorage."""
from __future__ import annotations

from datetime import timedelta
from typing import BinaryIO, Optional

import structlog

from app.domain.ports.object_storage import IObjectStorage
from app.infrastructure.resilience import retry_with_backoff, circuit
from app.infrastructure.s3_client import get_s3_client
from app.config import settings

logger = structlog.get_logger()


class S3Adapter(IObjectStorage):
    def __init__(self):
        self.client = get_s3_client()
        self.bucket = settings.s3_bucket

    @retry_with_backoff(max_attempts=3, initial_delay=1.0, max_delay=8.0)
    @circuit(failure_threshold=3, recovery_timeout=120)
    async def upload(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> str:
        if hasattr(data, "read"):
            body = data.read()
        else:
            body = data

        extra_args = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = {str(k): str(v) for k, v in metadata.items()}

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body,
            **extra_args,
        )
        logger.info("s3_upload_complete", key=key, size=len(body))
        return f"s3://{self.bucket}/{key}"

    @retry_with_backoff(max_attempts=3, initial_delay=1.0, max_delay=8.0)
    @circuit(failure_threshold=3, recovery_timeout=120)
    async def download(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        data = response["Body"].read()
        logger.info("s3_download_complete", key=key, size=len(data))
        return data

    def _presign_seconds(self, expires_in: timedelta) -> int:
        return int(expires_in.total_seconds())

    @retry_with_backoff(max_attempts=3, initial_delay=1.0, max_delay=8.0)
    @circuit(failure_threshold=3, recovery_timeout=120)
    async def generate_presigned_url(self, key: str, expires_in: timedelta) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=self._presign_seconds(expires_in),
        )

    @retry_with_backoff(max_attempts=3, initial_delay=1.0, max_delay=8.0)
    @circuit(failure_threshold=3, recovery_timeout=120)
    async def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False
