from datetime import datetime
from uuid import uuid4

from app.application.dtos.correlation import CorrelationCommand, YearOverYearCommand
from app.application.use_cases.correlation import CorrelationUseCase, YearOverYearUseCase
from app.domain.ports.correlation_repository import ICorrelationRepository
from app.domain.value_objects.tenant_id import TenantId


class _StubCorrelationRepo(ICorrelationRepository):
    def __init__(self):
        self.data = []
        self.yoy = {}

    def fetch_correlation_data(self, aoi_id, tenant_id, start_date: datetime):
        return self.data

    def fetch_year_over_year(self, aoi_id, tenant_id):
        return self.yoy


def test_correlation_use_case_returns_data():
    repo = _StubCorrelationRepo()
    repo.data = [
        {"date": "2026-W01", "ndvi": 0.5, "rvi": 0.4, "rain_mm": 12.0, "temp_avg": 25.0}
    ]
    use_case = CorrelationUseCase(repo)

    result = use_case.execute(
        CorrelationCommand(tenant_id=TenantId(value=uuid4()), aoi_id="aoi", weeks=4)
    )

    assert len(result.data) == 1
    assert result.data[0].ndvi == 0.5


def test_year_over_year_use_case_returns_result():
    repo = _StubCorrelationRepo()
    repo.yoy = {
        "current_year": 2026,
        "previous_year": 2025,
        "current_series": [{"week": 1, "ndvi": 0.5}],
        "previous_series": [{"week": 1, "ndvi": 0.4}],
    }
    use_case = YearOverYearUseCase(repo)

    result = use_case.execute(
        YearOverYearCommand(tenant_id=TenantId(value=uuid4()), aoi_id="aoi")
    )

    assert result.current_year == 2026
    assert result.current_series[0].ndvi == 0.5
