"""SQLAlchemy adapter for weather data (history)."""
from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.weather_data_repository import IWeatherDataRepository
from app.domain.value_objects.tenant_id import TenantId
import structlog

logger = structlog.get_logger()


class SQLAlchemyWeatherDataRepository(IWeatherDataRepository):
    def __init__(self, db: Session):
        self.db = db

    async def get_history(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 365,
    ) -> list[dict]:
        conditions = ["tenant_id = :tenant_id", "aoi_id = :aoi_id"]
        params = {
            "tenant_id": str(tenant_id.value),
            "aoi_id": str(aoi_id),
            "limit": limit,
        }

        if start_date:
            conditions.append("date >= :start_date")
            params["start_date"] = start_date
        if end_date:
            conditions.append("date <= :end_date")
            params["end_date"] = end_date

        where_clause = " AND ".join(conditions)

        sql = text(
            f"""
            SELECT date, temp_max, temp_min, precip_sum, et0_fao
            FROM derived_weather_daily
            WHERE {where_clause}
            ORDER BY date DESC
            LIMIT :limit
            """
        )

        try:
            result = self.db.execute(sql, params)
            return [dict(row._mapping) for row in result]
        except Exception as exc:
            logger.warning("weather_table_query_failed", exc_info=exc)
            return []
