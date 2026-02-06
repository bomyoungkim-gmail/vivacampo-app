"""Local filesystem adapter implementing IObjectStorage."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import BinaryIO, Optional

import structlog

from app.domain.ports.object_storage import IObjectStorage

logger = structlog.get_logger()


class LocalFileSystemAdapter(IObjectStorage):
    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> str:
        target = self.base_path / key
        target.parent.mkdir(parents=True, exist_ok=True)

        if hasattr(data, "read"):
            body = data.read()
        else:
            body = data

        target.write_bytes(body)
        logger.info("local_storage_upload", key=key, size=len(body))
        return f"file://{target.as_posix()}"

    async def download(self, key: str) -> bytes:
        target = self.base_path / key
        data = target.read_bytes()
        logger.info("local_storage_download", key=key, size=len(data))
        return data

    async def generate_presigned_url(self, key: str, expires_in: timedelta) -> str:
        target = self.base_path / key
        return f"file://{target.as_posix()}"

    async def exists(self, key: str) -> bool:
        target = self.base_path / key
        return target.exists()
