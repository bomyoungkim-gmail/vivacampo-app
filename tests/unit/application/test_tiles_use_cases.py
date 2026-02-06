import asyncio
from uuid import uuid4

from app.application.dtos.tiles import TileExportCommand, TileExportStatusCommand, TileJsonCommand, TileRequestCommand
from app.application.use_cases.tiles import (
    GetAoiExportStatusUseCase,
    GetAoiTileJsonUseCase,
    GetAoiTileUseCase,
    RequestAoiExportUseCase,
)
from app.domain.value_objects.tenant_id import TenantId


class _StubSpatialRepo:
    def __init__(self, exists=True):
        self._exists = exists

    async def exists(self, tenant_id, aoi_id):
        return self._exists

    async def get_tilejson_metadata(self, tenant_id, aoi_id):
        if not self._exists:
            return None
        return {
            "id": aoi_id,
            "name": "AOI Test",
            "minx": 0.0,
            "miny": 0.0,
            "maxx": 1.0,
            "maxy": 1.0,
            "cx": 0.5,
            "cy": 0.5,
        }

    async def get_geojson(self, tenant_id, aoi_id):
        return {"type": "Polygon", "coordinates": []}


class _StubStorage:
    def __init__(self, exists=False):
        self._exists = exists
        self.urls = []

    async def exists(self, key):
        return self._exists

    async def generate_presigned_url(self, key, expires_in):
        url = f"https://example.com/{key}"
        self.urls.append(url)
        return url

    async def upload(self, key, data, content_type="application/octet-stream", metadata=None):
        return f"s3://bucket/{key}"

    async def download(self, key):
        return b"data"


def test_get_aoi_tile_use_case():
    tenant_id = TenantId(value=uuid4())
    aoi_id = uuid4()
    repo = _StubSpatialRepo(exists=True)
    use_case = GetAoiTileUseCase(repo)

    async def run():
        return await use_case.execute(
            TileRequestCommand(
                tenant_id=tenant_id,
                aoi_id=aoi_id,
                z=1,
                x=2,
                y=3,
                index="ndvi",
            )
        )

    result = asyncio.run(run())
    assert result.url
    assert result.index == "ndvi"


def test_get_tilejson_use_case():
    tenant_id = TenantId(value=uuid4())
    aoi_id = uuid4()
    repo = _StubSpatialRepo(exists=True)
    use_case = GetAoiTileJsonUseCase(repo, api_base_url="http://api", cdn_enabled=True, cdn_tiles_url="http://cdn")

    async def run():
        return await use_case.execute(
            TileJsonCommand(tenant_id=tenant_id, aoi_id=aoi_id, index="ndvi")
        )

    result = asyncio.run(run())
    assert result["tiles"][0].startswith("http://cdn")


def test_request_export_use_case_cached():
    tenant_id = TenantId(value=uuid4())
    aoi_id = uuid4()
    repo = _StubSpatialRepo(exists=True)
    storage = _StubStorage(exists=True)
    use_case = RequestAoiExportUseCase(repo=repo, storage=storage)

    async def run():
        return await use_case.execute(
            TileExportCommand(tenant_id=tenant_id, aoi_id=aoi_id, index="ndvi")
        )

    result = asyncio.run(run())
    assert result.status == "ready"
    assert result.download_url


def test_export_status_use_case_processing():
    tenant_id = TenantId(value=uuid4())
    aoi_id = uuid4()
    storage = _StubStorage(exists=False)
    use_case = GetAoiExportStatusUseCase(storage=storage)

    async def run():
        return await use_case.execute(
            TileExportStatusCommand(tenant_id=tenant_id, aoi_id=aoi_id, index="ndvi")
        )

    result = asyncio.run(run())
    assert result.status == "processing"
