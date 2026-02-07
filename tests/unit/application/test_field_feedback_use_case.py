import asyncio
from uuid import uuid4

import pytest

from app.application.dtos.aois import FieldFeedbackCommand
from app.application.use_cases.aois import CreateFieldFeedbackUseCase
from app.domain.entities.aoi import AOI
from app.domain.ports.aoi_repository import IAOIRepository
from app.domain.ports.field_feedback_repository import IFieldFeedbackRepository
from app.domain.value_objects.area_hectares import AreaHectares
from app.domain.value_objects.geometry_wkt import GeometryWkt
from app.domain.value_objects.tenant_id import TenantId


class _StubAoiRepo(IAOIRepository):
    def __init__(self, aoi: AOI | None):
        self.aoi = aoi

    async def create(self, aoi: AOI) -> AOI:
        raise NotImplementedError

    async def get_by_id(self, tenant_id, aoi_id):
        if self.aoi and self.aoi.id == aoi_id:
            return self.aoi
        return None

    async def update(self, tenant_id, aoi_id, name=None, use_type=None, status=None, geometry_wkt=None):
        raise NotImplementedError

    async def delete(self, tenant_id, aoi_id):
        raise NotImplementedError

    async def list_by_tenant(self, tenant_id, farm_id=None, status=None, limit=100):
        raise NotImplementedError

    async def normalize_geometry(self, geometry_wkt: str):
        raise NotImplementedError


class _StubFeedbackRepo(IFieldFeedbackRepository):
    def __init__(self):
        self.created = None

    async def create(self, tenant_id, aoi_id, feedback_type, message, created_by_membership_id):
        self.created = {
            "tenant_id": tenant_id,
            "aoi_id": aoi_id,
            "feedback_type": feedback_type,
            "message": message,
            "created_by_membership_id": created_by_membership_id,
        }
        return uuid4()


def test_create_field_feedback_requires_aoi():
    use_case = CreateFieldFeedbackUseCase(_StubAoiRepo(None), _StubFeedbackRepo())
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(
            FieldFeedbackCommand(
                tenant_id=tenant_id,
                aoi_id=uuid4(),
                feedback_type="ISSUE",
                message="Test",
                created_by_membership_id=uuid4(),
            )
        )

    with pytest.raises(ValueError, match="AOI_NOT_FOUND"):
        asyncio.run(run())


def test_create_field_feedback_ok():
    tenant_id = TenantId(value=uuid4())
    aoi = AOI(
        tenant_id=tenant_id,
        farm_id=uuid4(),
        name="AOI",
        use_type="CROP",
        status="ACTIVE",
        geometry_wkt=GeometryWkt(value="POLYGON ((0 0, 0 1, 1 1, 0 0))"),
        area_hectares=AreaHectares(value=10.0),
    )
    feedback_repo = _StubFeedbackRepo()
    use_case = CreateFieldFeedbackUseCase(_StubAoiRepo(aoi), feedback_repo)

    async def run():
        return await use_case.execute(
            FieldFeedbackCommand(
                tenant_id=tenant_id,
                aoi_id=aoi.id,
                feedback_type="FALSE_POSITIVE",
                message="Cloud shadow",
                created_by_membership_id=uuid4(),
            )
        )

    result = asyncio.run(run())
    assert result.id is not None
    assert feedback_repo.created["feedback_type"] == "FALSE_POSITIVE"
