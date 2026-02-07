"""SQLAlchemy adapter for yield forecasts."""
from __future__ import annotations

from uuid import UUID

from app.domain.ports.yield_forecast_repository import IYieldForecastRepository
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.adapters.persistence.sqlalchemy.base_repository import BaseSQLAlchemyRepository


class SQLAlchemyYieldForecastRepository(IYieldForecastRepository, BaseSQLAlchemyRepository):
    async def get_latest_by_aoi(self, tenant_id: TenantId, aoi_id: UUID) -> dict | None:
        sql = """
            SELECT index_p10, index_p50, index_p90, confidence, season_year
            FROM yield_forecasts
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
            ORDER BY season_year DESC, created_at DESC
            LIMIT 1
        """
        return self._execute_query(
            sql,
            {"tenant_id": str(tenant_id.value), "aoi_id": str(aoi_id)},
            fetch_one=True,
        )

    async def get_tenant_summary(self, tenant_id: TenantId) -> dict | None:
        sql = """
            SELECT
                AVG(index_p10) AS p10,
                AVG(index_p50) AS p50,
                AVG(index_p90) AS p90
            FROM yield_forecasts
            WHERE tenant_id = :tenant_id
        """
        row = self._execute_query(sql, {"tenant_id": str(tenant_id.value)}, fetch_one=True)
        if not row or row["p50"] is None:
            return None
        return {"p10": row["p10"], "p50": row["p50"], "p90": row["p90"]}
