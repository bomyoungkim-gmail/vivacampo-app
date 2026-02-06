import asyncio
import shutil
from pathlib import Path
from uuid import uuid4

from app.infrastructure.adapters.storage.local_fs_adapter import LocalFileSystemAdapter


def test_local_fs_upload_download():
    repo_root = Path(__file__).resolve().parents[3]
    tmp_root = repo_root / "tests" / ".tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    tmp_dir = tmp_root / f"local_fs_{uuid4().hex}"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        adapter = LocalFileSystemAdapter(tmp_dir)

        async def run():
            await adapter.upload("file.txt", b"hello")
            data = await adapter.download("file.txt")
            return data

        data = asyncio.run(run())
        assert data == b"hello"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
