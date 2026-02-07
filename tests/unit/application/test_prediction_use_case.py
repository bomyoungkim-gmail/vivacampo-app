import asyncio
from uuid import uuid4

import pytest

from app.application.dtos.aois import PredictionCommand
from app.application.use_cases.aois import GetPredictionUseCase
from app.domain.ports.yield_forecast_repository import IYieldForecastRepository
from app.domain.value_objects.tenant_id import TenantId


class _StubYieldRepo(IYieldForecastRepository):
    def __init__(self, latest=None, summary=None):
        self.latest = latest
        self.summary = summary

    async def get_latest_by_aoi(self, tenant_id, aoi_id):
        return self.latest

    async def get_tenant_summary(self, tenant_id):
        return self.summary


def test_prediction_returns_latest():
    repo = _StubYieldRepo(latest={"index_p10": 10, "index_p50": 20, "index_p90": 30, "confidence": 0.7})
    use_case = GetPredictionUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(PredictionCommand(tenant_id=tenant_id, aoi_id=uuid4(), metric_type="yield"))

    result = asyncio.run(run())
    assert result.p50 == 20
    assert result.source == "aoi_forecast"


def test_prediction_fallback_summary():
    repo = _StubYieldRepo(latest=None, summary={"p10": 5, "p50": 6, "p90": 7})
    use_case = GetPredictionUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(PredictionCommand(tenant_id=tenant_id, aoi_id=uuid4(), metric_type="yield"))

    result = asyncio.run(run())
    assert result.source == "tenant_average"


def test_prediction_insufficient_data():
    repo = _StubYieldRepo(latest=None, summary=None)
    use_case = GetPredictionUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(PredictionCommand(tenant_id=tenant_id, aoi_id=uuid4(), metric_type="yield"))

    with pytest.raises(ValueError, match="INSUFFICIENT_DATA"):
        asyncio.run(run())
