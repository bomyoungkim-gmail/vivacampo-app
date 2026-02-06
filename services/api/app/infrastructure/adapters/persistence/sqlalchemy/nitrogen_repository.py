"""SQLAlchemy adapter for nitrogen repository."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.nitrogen_repository import INitrogenRepository
from app.domain.value_objects.tenant_id import TenantId


class SQLAlchemyNitrogenRepository(INitrogenRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_latest_indices(self, tenant_id: TenantId, aoi_id: str) -> dict:
        sql = text(
            """
            SELECT ndvi_mean, ndre_mean, reci_mean, year, week
            FROM derived_assets
            WHERE aoi_id = :aoi_id AND tenant_id = :tenant_id
            ORDER BY year DESC, week DESC
            LIMIT 1
            """
        )
        result = self.db.execute(
            sql,
            {"aoi_id": aoi_id, "tenant_id": str(tenant_id.value)},
        ).first()
        if result:
            return {
                "ndvi_mean": result.ndvi_mean,
                "ndre_mean": result.ndre_mean,
                "reci_mean": result.reci_mean,
            }
        return {}
