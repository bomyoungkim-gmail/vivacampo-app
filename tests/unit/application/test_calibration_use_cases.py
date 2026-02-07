import asyncio
from datetime import date
from uuid import uuid4

import pytest

from app.application.dtos.aois import FieldCalibrationCreateCommand, CalibrationCommand
from app.application.use_cases.aois import CreateFieldCalibrationUseCase, GetCalibrationUseCase
from app.domain.entities.aoi import AOI
from app.domain.ports.aoi_repository import IAOIRepository
from app.domain.ports.field_calibration_repository import IFieldCalibrationRepository
from app.domain.ports.aoi_data_repository import IAoiDataRepository
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


class _StubCalibrationRepo(IFieldCalibrationRepository):
    def __init__(self):
        self.created = []
        self.last = None

    async def create(self, tenant_id, aoi_id, observed_date, metric_type, value, unit, source):
        calibration_id = uuid4()
        self.last = {
            "id": calibration_id,
            "aoi_id": aoi_id,
            "observed_date": observed_date,
            "metric_type": metric_type,
            "value": value,
            "unit": unit,
            "source": source,
        }
        self.created.append(self.last)
        return calibration_id

    async def list_by_aoi_metric(self, tenant_id, aoi_id, metric_type):
        return [
            {"observed_date": date(2026, 2, 1), "value": 100.0},
            {"observed_date": date(2026, 2, 8), "value": 140.0},
        ]


class _StubAoiDataRepo(IAoiDataRepository):
    async def get_latest_assets(self, tenant_id, aoi_id):
        raise NotImplementedError

    async def get_history(self, tenant_id, aoi_id, limit=52):
        raise NotImplementedError

    async def get_index_for_week(self, tenant_id, aoi_id, year, week):
        if week == date(2026, 2, 1).isocalendar().week:
            return {"ndvi_mean": 0.6}
        return {"ndvi_mean": 0.7}


def test_create_field_calibration_requires_aoi():
    use_case = CreateFieldCalibrationUseCase(_StubAoiRepo(None), _StubCalibrationRepo())
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(
            FieldCalibrationCreateCommand(
                tenant_id=tenant_id,
                aoi_id=uuid4(),
                observed_date="2026-02-01",
                metric_type="biomass",
                value=100.0,
                unit="kg_ha",
            )
        )

    with pytest.raises(ValueError, match="AOI_NOT_FOUND"):
        asyncio.run(run())


def test_create_field_calibration_converts_sc_ha():
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
    repo = _StubCalibrationRepo()
    use_case = CreateFieldCalibrationUseCase(_StubAoiRepo(aoi), repo)

    async def run():
        return await use_case.execute(
            FieldCalibrationCreateCommand(
                tenant_id=tenant_id,
                aoi_id=aoi.id,
                observed_date="2026-02-01",
                metric_type="yield",
                value=10.0,
                unit="sc_ha",
            )
        )

    result = asyncio.run(run())
    assert result.unit == "kg_ha"
    assert repo.last["value"] == 600.0


def test_get_calibration_returns_regression():
    tenant_id = TenantId(value=uuid4())
    use_case = GetCalibrationUseCase(_StubCalibrationRepo(), _StubAoiDataRepo())

    async def run():
        return await use_case.execute(
            CalibrationCommand(
                tenant_id=tenant_id,
                aoi_id=uuid4(),
                metric_type="biomass",
            )
        )

    result = asyncio.run(run())
    assert result.sample_size == 2
    assert result.r2 >= 0.0
