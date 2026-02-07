"""Backward-compatible correlation service wrapper."""
from typing import List
from uuid import UUID

from app.application.dtos.correlation import CorrelationCommand, YearOverYearCommand
from app.application.use_cases.correlation import CorrelationUseCase, YearOverYearUseCase
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.adapters.persistence.sqlalchemy.correlation_repository import SQLAlchemyCorrelationRepository


class CorrelationService:
    def __init__(self, repo: SQLAlchemyCorrelationRepository):
        self.repo = repo

    def fetch_correlation_data(self, aoi_id: str, tenant_id: str, weeks: int) -> List[dict]:
        use_case = CorrelationUseCase(self.repo)
        result = use_case.execute(
            CorrelationCommand(tenant_id=TenantId(value=UUID(tenant_id)), aoi_id=aoi_id, weeks=weeks)
        )
        return [
            {
                "date": item.date,
                "ndvi": item.ndvi,
                "rvi": item.rvi,
                "rain_mm": item.rain_mm,
                "temp_avg": item.temp_avg,
            }
            for item in result.data
        ]

    def generate_insights(self, data: List[dict]) -> List[dict]:
        use_case = CorrelationUseCase(self.repo)
        # reusar logica interna passando lista ja calculada
        return use_case._generate_insights(data)

    def fetch_year_over_year(self, aoi_id: str, tenant_id: str) -> dict:
        use_case = YearOverYearUseCase(self.repo)
        result = use_case.execute(YearOverYearCommand(tenant_id=TenantId(value=UUID(tenant_id)), aoi_id=aoi_id))
        if not result:
            return {}
        return {
            "current_year": result.current_year,
            "previous_year": result.previous_year,
            "current_series": [{"week": item.week, "ndvi": item.ndvi} for item in result.current_series],
            "previous_series": [{"week": item.week, "ndvi": item.ndvi} for item in result.previous_series],
        }
