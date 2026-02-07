import pytest
from uuid import UUID

from app.application.dtos.aois import SimulateSplitCommand
from app.application.use_cases.aois import SimulateSplitUseCase
from app.domain.ports.aoi_spatial_repository import IAoiSpatialRepository
from app.domain.value_objects.tenant_id import TenantId


class _StubSpatialRepo(IAoiSpatialRepository):
    async def exists(self, tenant_id, aoi_id):
        raise NotImplementedError

    async def get_tilejson_metadata(self, tenant_id, aoi_id):
        raise NotImplementedError

    async def get_geojson(self, tenant_id, aoi_id):
        raise NotImplementedError

    async def simulate_split(self, tenant_id, geometry_wkt, mode, target_count):
        return [
            {"geometry_wkt": "MULTIPOLYGON (((0 0, 0 1, 1 1, 0 0)))", "area_ha": 2500.0},
            {"geometry_wkt": "MULTIPOLYGON (((1 1, 1 2, 2 2, 1 1)))", "area_ha": 1500.0},
        ]


@pytest.mark.asyncio
async def test_simulate_split_adds_warning():
    use_case = SimulateSplitUseCase(_StubSpatialRepo())
    result = await use_case.execute(
        SimulateSplitCommand(
            tenant_id=TenantId(value=UUID("00000000-0000-0000-0000-000000000001")),
            geometry_wkt="MULTIPOLYGON (((0 0, 0 1, 1 1, 0 0)))",
            mode="grid",
            target_count=2,
            max_area_ha=2000,
        )
    )
    assert len(result.polygons) == 2
    assert "talhao_1_exceeds_max_area" in result.warnings
