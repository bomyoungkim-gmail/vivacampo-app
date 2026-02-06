from uuid import uuid4

from app.application.dtos.nitrogen import GetNitrogenStatusCommand
from app.application.use_cases.nitrogen import GetNitrogenStatusUseCase
from app.domain.ports.nitrogen_repository import INitrogenRepository
from app.domain.value_objects.tenant_id import TenantId


class _StubNitrogenRepo(INitrogenRepository):
    def __init__(self, indices=None):
        self.indices = indices or {}

    def get_latest_indices(self, tenant_id, aoi_id):
        return self.indices


def test_nitrogen_use_case_deficient():
    repo = _StubNitrogenRepo({"ndvi_mean": 0.8, "ndre_mean": 0.4, "reci_mean": 1.0})
    use_case = GetNitrogenStatusUseCase(repo)

    result = use_case.execute(
        GetNitrogenStatusCommand(
            tenant_id=TenantId(value=uuid4()),
            aoi_id="aoi",
            base_url="http://localhost:8000",
        )
    )

    assert result.status == "DEFICIENT"
    assert result.zone_map_url.endswith("/v1/tiles/aois/aoi/{z}/{x}/{y}.png?index=srre")
