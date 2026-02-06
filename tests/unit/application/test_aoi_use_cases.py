import asyncio
from datetime import datetime
from uuid import uuid4

from app.application.dtos.aois import CreateAoiCommand, ListAoisCommand
from app.application.use_cases.aois import CreateAoiUseCase, ListAoisUseCase
from app.domain.entities.aoi import AOI
from app.domain.ports.aoi_repository import IAOIRepository
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

    async def update(
        self,
        tenant_id,
        aoi_id,
        name=None,
        use_type=None,
        status=None,
        geometry_wkt=None,
    ):
        aoi = await self.get_by_id(tenant_id, aoi_id)
        if not aoi:
            return None
        if name is not None:
            aoi.name = name
        if use_type is not None:
            aoi.use_type = use_type
        if status is not None:
            aoi.status = status
        if geometry_wkt is not None:
            aoi.geometry_wkt = geometry_wkt
        return aoi

    async def delete(self, tenant_id, aoi_id):
        for idx, aoi in enumerate(self.created):
            if aoi.tenant_id == tenant_id and aoi.id == aoi_id:
                del self.created[idx]
                return True
        return False

    async def list_by_tenant(self, tenant_id, farm_id=None, status=None, limit=100):
        return self.created


def test_create_aoi_use_case_returns_result():
    repo = _StubAoiRepo()
    use_case = CreateAoiUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(
            CreateAoiCommand(
                tenant_id=tenant_id,
                farm_id=uuid4(),
                name="Talhao 1",
                use_type="CROP",
                geometry_wkt="POLYGON ((0 0, 0 1, 1 1, 0 0))",
            )
        )

    result = asyncio.run(run())
    assert result.name == "Talhao 1"
    assert result.tenant_id == tenant_id.value


def test_list_aoi_use_case_returns_results():
    repo = _StubAoiRepo()
    use_case = ListAoisUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    repo.created.append(
        AOI(
            tenant_id=tenant_id,
            farm_id=uuid4(),
            name="Talhao 2",
            use_type="PASTURE",
            status="ACTIVE",
            geometry_wkt=GeometryWkt(value="POLYGON ((0 0, 0 1, 1 1, 0 0))"),
            area_hectares=AreaHectares(value=10.0),
            created_at=datetime.utcnow(),
        )
    )

    async def run():
        return await use_case.execute(ListAoisCommand(tenant_id=tenant_id))

    results = asyncio.run(run())
    assert len(results) == 1
    assert results[0].name == "Talhao 2"
