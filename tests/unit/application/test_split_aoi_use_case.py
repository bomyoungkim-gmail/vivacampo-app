import asyncio
from uuid import uuid4

import pytest

from app.application.dtos.aois import SplitAoiCommand, SplitPolygonInput
from app.application.use_cases.aois import SplitAoiUseCase
from app.domain.entities.aoi import AOI
from app.domain.ports.aoi_repository import IAOIRepository
from app.domain.ports.split_batch_repository import ISplitBatchRepository
from app.domain.value_objects.area_hectares import AreaHectares
from app.domain.value_objects.geometry_wkt import GeometryWkt
from app.domain.value_objects.tenant_id import TenantId


class _StubAoiRepo(IAOIRepository):
    def __init__(self):
        self.created = []

    async def create(self, aoi: AOI) -> AOI:
        self.created.append(aoi)
        return aoi

    async def get_by_id(self, tenant_id, aoi_id):
        for aoi in self.created:
            if aoi.tenant_id == tenant_id and aoi.id == aoi_id:
                return aoi
        return None

    async def update(self, tenant_id, aoi_id, name=None, use_type=None, status=None, geometry_wkt=None):
        raise NotImplementedError

    async def delete(self, tenant_id, aoi_id):
        raise NotImplementedError

    async def list_by_tenant(self, tenant_id, farm_id=None, status=None, limit=100):
        raise NotImplementedError

    async def normalize_geometry(self, geometry_wkt: str):
        return geometry_wkt, 10.0


class _StubSplitBatchRepo(ISplitBatchRepository):
    def __init__(self):
        self.by_key: dict[str, list[str]] = {}

    async def get_by_key(self, tenant_id, idempotency_key: str):
        value = self.by_key.get(idempotency_key)
        return value

    async def create(self, tenant_id, parent_aoi_id, idempotency_key, created_ids):
        self.by_key[idempotency_key] = created_ids


def test_split_aoi_use_case_creates_children():
    repo = _StubAoiRepo()
    use_case = SplitAoiUseCase(repo, _StubSplitBatchRepo())
    tenant_id = TenantId(value=uuid4())
    parent_id = uuid4()

    repo.created.append(
        AOI(
            id=parent_id,
            tenant_id=tenant_id,
            farm_id=uuid4(),
            name="Macro",
            use_type="CROP",
            status="ACTIVE",
            geometry_wkt=GeometryWkt(value="POLYGON ((0 0, 0 1, 1 1, 0 0))"),
            area_hectares=AreaHectares(value=10.0),
        )
    )

    async def run():
        return await use_case.execute(
            SplitAoiCommand(
                tenant_id=tenant_id,
                parent_aoi_id=parent_id,
                polygons=[
                    SplitPolygonInput(geometry_wkt="POLYGON ((0 0, 0 1, 1 1, 0 0))", name="Talhao 1"),
                    SplitPolygonInput(geometry_wkt="POLYGON ((1 1, 1 2, 2 2, 1 1))", name="Talhao 2"),
                ],
                max_area_ha=2000,
            )
        )

    result = asyncio.run(run())
    assert len(result.created_ids) == 2


def test_split_aoi_use_case_rejects_missing_parent():
    repo = _StubAoiRepo()
    use_case = SplitAoiUseCase(repo, _StubSplitBatchRepo())
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(
            SplitAoiCommand(
                tenant_id=tenant_id,
                parent_aoi_id=uuid4(),
                polygons=[SplitPolygonInput(geometry_wkt="POLYGON ((0 0, 0 1, 1 1, 0 0))")],
                max_area_ha=2000,
            )
        )

    with pytest.raises(ValueError, match="PARENT_AOI_NOT_FOUND"):
        asyncio.run(run())


def test_split_aoi_use_case_idempotent():
    repo = _StubAoiRepo()
    batch_repo = _StubSplitBatchRepo()
    use_case = SplitAoiUseCase(repo, batch_repo)
    tenant_id = TenantId(value=uuid4())
    parent_id = uuid4()

    repo.created.append(
        AOI(
            id=parent_id,
            tenant_id=tenant_id,
            farm_id=uuid4(),
            name="Macro",
            use_type="CROP",
            status="ACTIVE",
            geometry_wkt=GeometryWkt(value="POLYGON ((0 0, 0 1, 1 1, 0 0))"),
            area_hectares=AreaHectares(value=10.0),
        )
    )

    async def run():
        return await use_case.execute(
            SplitAoiCommand(
                tenant_id=tenant_id,
                parent_aoi_id=parent_id,
                polygons=[SplitPolygonInput(geometry_wkt="POLYGON ((0 0, 0 1, 1 1, 0 0))")],
                max_area_ha=2000,
                idempotency_key="key-1",
            )
        )

    first = asyncio.run(run())
    second = asyncio.run(run())
    assert first.created_ids == second.created_ids
    assert second.idempotent is True
