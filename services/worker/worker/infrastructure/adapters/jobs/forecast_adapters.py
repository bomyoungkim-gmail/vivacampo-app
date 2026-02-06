"""Adapters for FORECAST_WEEK."""
from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from worker.domain.ports.forecast_provider import (
    ForecastObservationsRepository,
    SeasonRepository,
    YieldForecastRepository,
)


class SqlSeasonRepository(SeasonRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_active_season(self, *, tenant_id: str, aoi_id: str) -> dict | None:
        sql = text(
            """
            SELECT id, crop_type, planted_date, expected_harvest_date
            FROM seasons
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
              AND status = 'ACTIVE'
            ORDER BY planted_date DESC
            LIMIT 1
            """
        )
        row = self._db.execute(sql, {"tenant_id": tenant_id, "aoi_id": aoi_id}).fetchone()
        if not row:
            return None
        return {
            "id": row.id,
            "crop_type": row.crop_type,
            "planted_date": row.planted_date,
            "expected_harvest_date": row.expected_harvest_date,
        }


class SqlForecastObservationsRepository(ForecastObservationsRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_observations(self, *, tenant_id: str, aoi_id: str) -> list[dict]:
        sql = text(
            """
            SELECT year, week, ndvi_mean, ndvi_p90
            FROM observations_weekly
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
              AND status = 'OK'
            ORDER BY year, week
            """
        )
        rows = self._db.execute(sql, {"tenant_id": tenant_id, "aoi_id": aoi_id}).fetchall()
        return [
            {"year": row.year, "week": row.week, "ndvi_mean": row.ndvi_mean, "ndvi_p90": row.ndvi_p90}
            for row in rows
        ]


class SqlYieldForecastRepository(YieldForecastRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_historical_yields(self, *, tenant_id: str, aoi_id: str, limit: int) -> list[float]:
        sql = text(
            """
            SELECT actual_yield_kg_ha
            FROM yield_forecasts
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
              AND actual_yield_kg_ha IS NOT NULL
            ORDER BY created_at DESC
            LIMIT :limit
            """
        )
        rows = self._db.execute(
            sql,
            {"tenant_id": tenant_id, "aoi_id": aoi_id, "limit": limit},
        ).fetchall()
        return [row.actual_yield_kg_ha for row in rows]

    def save_forecast(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        season_id: str,
        year: int,
        week: int,
        estimated_yield: float,
        confidence: str,
        evidence: dict,
        method: str,
        model_version: str,
    ) -> None:
        sql = text(
            """
            INSERT INTO yield_forecasts
            (tenant_id, aoi_id, season_id, year, week, method, estimated_yield_kg_ha,
             confidence, model_version, evidence_json)
            VALUES (:tenant_id, :aoi_id, :season_id, :year, :week, :method,
                    :estimated_yield, :confidence, :model_version, :evidence)
            ON CONFLICT (tenant_id, aoi_id, season_id, year, week) DO UPDATE
            SET estimated_yield_kg_ha = :estimated_yield,
                confidence = :confidence,
                evidence_json = :evidence,
                updated_at = now()
            """
        )
        self._db.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "aoi_id": aoi_id,
                "season_id": season_id,
                "year": year,
                "week": week,
                "method": method,
                "estimated_yield": estimated_yield,
                "confidence": confidence,
                "model_version": model_version,
                "evidence": json.dumps(evidence),
            },
        )
        self._db.commit()
