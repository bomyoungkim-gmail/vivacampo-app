"""Adapters for ALERTS_WEEK."""
from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from worker.domain.ports.alerts_provider import AlertRepository, AlertsObservationsRepository, TenantSettingsRepository


class SqlTenantSettingsRepository(TenantSettingsRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_min_valid_pixel_ratio(self, *, tenant_id: str) -> float:
        sql = text("SELECT min_valid_pixel_ratio FROM tenant_settings WHERE tenant_id = :tenant_id")
        row = self._db.execute(sql, {"tenant_id": tenant_id}).fetchone()
        return row.min_valid_pixel_ratio if row else 0.15


class SqlAlertsObservationsRepository(AlertsObservationsRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_observation(self, *, tenant_id: str, aoi_id: str, year: int, week: int) -> dict | None:
        sql = text(
            """
            SELECT status, valid_pixel_ratio, ndvi_mean, ndvi_p10, anomaly
            FROM observations_weekly
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
              AND year = :year AND week = :week
            """
        )
        row = self._db.execute(
            sql,
            {"tenant_id": tenant_id, "aoi_id": aoi_id, "year": year, "week": week},
        ).fetchone()
        if not row:
            return None
        return {
            "status": row.status,
            "valid_pixel_ratio": row.valid_pixel_ratio,
            "ndvi_mean": row.ndvi_mean,
            "ndvi_p10": row.ndvi_p10,
            "anomaly": row.anomaly,
        }

    def get_previous_observation(self, *, tenant_id: str, aoi_id: str, year: int, week: int) -> dict | None:
        sql = text(
            """
            SELECT ndvi_mean
            FROM observations_weekly
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
              AND (year = :year AND week < :week) OR (year = :prev_year AND week > :week)
            ORDER BY year DESC, week DESC
            LIMIT 1
            """
        )
        row = self._db.execute(
            sql,
            {"tenant_id": tenant_id, "aoi_id": aoi_id, "year": year, "week": week, "prev_year": year - 1},
        ).fetchone()
        if not row:
            return None
        return {"ndvi_mean": row.ndvi_mean}

    def count_persistent_anomalies(self, *, tenant_id: str, aoi_id: str, year: int, week: int) -> int:
        sql = text(
            """
            SELECT COUNT(*) as count
            FROM observations_weekly
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
              AND year = :year AND week <= :week AND week > :week - 3
              AND anomaly < -0.05
            """
        )
        row = self._db.execute(
            sql,
            {"tenant_id": tenant_id, "aoi_id": aoi_id, "year": year, "week": week},
        ).fetchone()
        return row.count if row else 0


class SqlAlertRepository(AlertRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_existing(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
        alert_type: str,
    ) -> dict | None:
        sql = text(
            """
            SELECT id, status
            FROM alerts
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
              AND year = :year AND week = :week
              AND alert_type = :alert_type
              AND status IN ('OPEN', 'ACK')
            """
        )
        row = self._db.execute(
            sql,
            {"tenant_id": tenant_id, "aoi_id": aoi_id, "year": year, "week": week, "alert_type": alert_type},
        ).fetchone()
        if row:
            return {"id": row.id, "status": row.status}
        return None

    def update_alert(self, *, alert_id: str, severity: str, confidence: str, evidence: dict) -> None:
        sql = text(
            """
            UPDATE alerts
            SET severity = :severity, confidence = :confidence,
                evidence_json = :evidence, updated_at = now()
            WHERE id = :alert_id
            """
        )
        self._db.execute(
            sql,
            {
                "alert_id": alert_id,
                "severity": severity,
                "confidence": confidence,
                "evidence": json.dumps(evidence),
            },
        )
        self._db.commit()

    def create_alert(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
        alert_type: str,
        severity: str,
        confidence: str,
        evidence: dict,
    ) -> None:
        sql = text(
            """
            INSERT INTO alerts
            (tenant_id, aoi_id, year, week, alert_type, status, severity, confidence, evidence_json)
            SELECT :tenant_id, :aoi_id, :year, :week, :alert_type, 'OPEN', :severity, :confidence, :evidence
            WHERE NOT EXISTS (
                SELECT 1
                FROM alerts
                WHERE tenant_id = :tenant_id
                  AND aoi_id = :aoi_id
                  AND year = :year
                  AND week = :week
                  AND alert_type = :alert_type
                  AND status IN ('OPEN', 'ACK')
            )
            """
        )
        self._db.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "aoi_id": aoi_id,
                "year": year,
                "week": week,
                "alert_type": alert_type,
                "severity": severity,
                "confidence": confidence,
                "evidence": json.dumps(evidence),
            },
        )
        self._db.commit()
