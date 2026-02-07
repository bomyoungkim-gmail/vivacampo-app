"""SQLAlchemy adapter for field calibrations."""
from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.field_calibration_repository import IFieldCalibrationRepository
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.adapters.persistence.sqlalchemy.base_repository import BaseSQLAlchemyRepository


class SQLAlchemyFieldCalibrationRepository(IFieldCalibrationRepository, BaseSQLAlchemyRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    async def create(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        observed_date: date,
        metric_type: str,
        value: float,
        unit: str,
        source: str,
    ) -> UUID:
        sql = text(
            """
            WITH existing AS (
                SELECT COALESCE(MAX(version), 0) AS max_version
                FROM field_calibrations
                WHERE tenant_id = :tenant_id
                  AND aoi_id = :aoi_id
                  AND observed_date = :observed_date
                  AND metric_type = :metric_type
            ),
            deactivate AS (
                UPDATE field_calibrations
                SET is_active = false
                WHERE tenant_id = :tenant_id
                  AND aoi_id = :aoi_id
                  AND observed_date = :observed_date
                  AND metric_type = :metric_type
                  AND is_active = true
            )
            INSERT INTO field_calibrations (
                tenant_id, aoi_id, observed_date, metric_type, value, unit, source, version, is_active
            )
            VALUES (
                :tenant_id, :aoi_id, :observed_date, :metric_type, :value, :unit, :source,
                (SELECT max_version + 1 FROM existing), true
            )
            RETURNING id
            """
        )
        result = self.db.execute(
            sql,
            {
                "tenant_id": str(tenant_id.value),
                "aoi_id": str(aoi_id),
                "observed_date": observed_date,
                "metric_type": metric_type,
                "value": value,
                "unit": unit,
                "source": source,
            },
        )
        self.db.commit()
        return result.fetchone()[0]

    async def list_by_aoi_metric(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        metric_type: str,
    ) -> list[dict]:
        sql = """
            SELECT id, observed_date, metric_type, value, unit, source, version
            FROM field_calibrations
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id AND metric_type = :metric_type
              AND is_active = true
            ORDER BY observed_date ASC
        """
        return self._execute_query(
            sql,
            {"tenant_id": str(tenant_id.value), "aoi_id": str(aoi_id), "metric_type": metric_type},
        )
