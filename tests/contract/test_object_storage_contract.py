import asyncio
import tempfile
from pathlib import Path

from app.infrastructure.adapters.storage.local_fs_adapter import LocalFileSystemAdapter


def test_local_storage_contract_upload_download_exists():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalFileSystemAdapter(tmpdir)
        key = "contract/test.bin"
        payload = b"local-storage"

        async def run():
            uri = await storage.upload(key=key, data=payload, content_type="application/octet-stream")
            assert uri.startswith("file://")
            assert await storage.exists(key) is True
            data = await storage.download(key)
            assert data == payload

        asyncio.run(run())
