import asyncio
from pathlib import Path
import shutil

from app.infrastructure.adapters.storage.local_fs_adapter import LocalFileSystemAdapter


def test_local_storage_contract_upload_download_exists():
    base_dir = Path(".tmp") / "tests" / "local_fs_contract"
    if base_dir.exists():
        shutil.rmtree(base_dir, ignore_errors=True)
    base_dir.mkdir(parents=True, exist_ok=True)
    try:
        storage = LocalFileSystemAdapter(base_dir)
        key = "contract_test.bin"
        payload = b"local-storage"

        async def run():
            uri = await storage.upload(key=key, data=payload, content_type="application/octet-stream")
            assert uri.startswith("file://")
            assert await storage.exists(key) is True
            data = await storage.download(key)
            assert data == payload

        asyncio.run(run())
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)
