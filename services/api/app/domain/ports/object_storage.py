"""Object storage port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import BinaryIO, Optional


class IObjectStorage(ABC):
    @abstractmethod
    async def upload(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> str:
        """Upload object and return its URI."""
        raise NotImplementedError

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """Download object data."""
        raise NotImplementedError

    @abstractmethod
    async def generate_presigned_url(self, key: str, expires_in: timedelta) -> str:
        """Generate a presigned URL for temporary access."""
        raise NotImplementedError

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if an object exists."""
        raise NotImplementedError
