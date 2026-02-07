"""SQLAlchemy adapter for nitrogen repository."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.ports.nitrogen_repository import INitrogenRepository
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.adapters.persistence.sqlalchemy.base_repository import BaseSQLAlchemyRepository


class SQLAlchemyNitrogenRepository(INitrogenRepository, BaseSQLAlchemyRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_latest_indices(self, tenant_id: TenantId, aoi_id: str) -> dict:
        sql = """
            SELECT ndvi_mean, ndre_mean, reci_mean, year, week
            FROM derived_assets
            WHERE aoi_id = :aoi_id AND tenant_id = :tenant_id
            ORDER BY year DESC, week DESC
            LIMIT 1
            """
        result = self._execute_query(
            sql,
            {"aoi_id": aoi_id, "tenant_id": str(tenant_id.value)},
            fetch_one=True,
        )
        if result:
            return {
                "ndvi_mean": result["ndvi_mean"],
                "ndre_mean": result["ndre_mean"],
                "reci_mean": result["reci_mean"],
            }
        return {}
