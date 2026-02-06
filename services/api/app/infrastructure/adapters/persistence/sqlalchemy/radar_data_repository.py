"""SQLAlchemy adapter for radar data (history)."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.radar_data_repository import IRadarDataRepository
from app.domain.value_objects.tenant_id import TenantId
import structlog

logger = structlog.get_logger()


class SQLAlchemyRadarDataRepository(IRadarDataRepository):
    def __init__(self, db: Session):
        self.db = db

    async def get_history(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        year: Optional[int] = None,
        limit: int = 52,
    ) -> list[dict]:
        conditions = ["tenant_id = :tenant_id", "aoi_id = :aoi_id"]
        params = {
            "tenant_id": str(tenant_id.value),
            "aoi_id": str(aoi_id),
            "limit": limit,
        }

        if year:
            conditions.append("year = :year")
            params["year"] = year

        where_clause = " AND ".join(conditions)

        sql = text(
            f"""
            SELECT year, week, rvi_mean, rvi_std, ratio_mean, ratio_std, rvi_s3_uri, ratio_s3_uri
            FROM derived_radar_assets
            WHERE {where_clause}
            ORDER BY year DESC, week DESC
            LIMIT :limit
            """
        )

        try:
            result = self.db.execute(sql, params)
            return [dict(row._mapping) for row in result]
        except Exception as exc:
            logger.warning("radar_table_query_failed", exc_info=exc)
            return []
