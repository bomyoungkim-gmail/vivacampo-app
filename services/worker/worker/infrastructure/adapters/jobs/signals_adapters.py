"""Adapters for SIGNALS_WEEK."""
from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from worker.config import settings
from worker.domain.ports.signals_provider import AoiInfoRepository, SignalRepository, SignalsObservationsRepository


class SqlSignalsObservationsRepository(SignalsObservationsRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_recent(self, *, tenant_id: str, aoi_id: str, limit: int) -> list[dict]:
        sql = text(
            """
            SELECT year, week, ndvi_mean, ndvi_p10, ndvi_p50, ndvi_p90, ndvi_std,
                   baseline, anomaly, valid_pixel_ratio, status
            FROM observations_weekly
            WHERE tenant_id = :tenant_id
              AND aoi_id = :aoi_id
              AND status = 'OK'
            ORDER BY year DESC, week DESC
            LIMIT :limit
            """
        )
        result = self._db.execute(sql, {"tenant_id": tenant_id, "aoi_id": aoi_id, "limit": limit})

        observations = []
        for row in result:
            observations.append(
                {
                    "year": row.year,
                    "week": row.week,
                    "ndvi_mean": row.ndvi_mean,
                    "ndvi_p10": row.ndvi_p10,
                    "ndvi_p50": row.ndvi_p50,
                    "ndvi_p90": row.ndvi_p90,
                    "ndvi_std": row.ndvi_std,
                    "baseline": row.baseline,
                    "anomaly": row.anomaly,
                    "valid_pixel_ratio": row.valid_pixel_ratio,
                }
            )

        return list(reversed(observations))


class SqlAoiInfoRepository(AoiInfoRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_use_type(self, *, tenant_id: str, aoi_id: str) -> str:
        sql = text("SELECT use_type FROM aois WHERE id = :aoi_id AND tenant_id = :tenant_id")
        row = self._db.execute(sql, {"aoi_id": aoi_id, "tenant_id": tenant_id}).fetchone()
        return row.use_type if row else "PASTURE"


class SqlSignalRepository(SignalRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_existing(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
        signal_type: str,
        pipeline_version: str,
    ) -> dict | None:
        sql = text(
            """
            SELECT id, status
            FROM opportunity_signals
            WHERE tenant_id = :tenant_id
              AND aoi_id = :aoi_id
              AND year = :year
              AND week = :week
              AND signal_type = :signal_type
              AND pipeline_version = :pipeline_version
            """
        )
        row = self._db.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "aoi_id": aoi_id,
                "year": year,
                "week": week,
                "signal_type": signal_type,
                "pipeline_version": pipeline_version,
            },
        ).fetchone()
        if row:
            return {"id": row.id, "status": row.status}
        return None

    def update_signal(self, *, signal_id: str, score: float, evidence: dict, features: dict) -> None:
        sql = text(
            """
            UPDATE opportunity_signals
            SET score = :score,
                evidence_json = :evidence,
                features_json = :features,
                updated_at = now()
            WHERE id = :signal_id
            """
        )
        self._db.execute(
            sql,
            {
                "signal_id": signal_id,
                "score": score,
                "evidence": json.dumps(evidence),
                "features": json.dumps(features),
            },
        )
        self._db.commit()

    def create_signal(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
        signal_type: str,
        severity: str,
        confidence: str,
        score: float,
        evidence: dict,
        features: dict,
        recommended_actions: list,
        created_at,
        pipeline_version: str,
        model_version: str,
        change_method: str,
    ) -> None:
        sql = text(
            """
            INSERT INTO opportunity_signals
            (tenant_id, aoi_id, year, week, pipeline_version, signal_type, status,
             severity, confidence, score, model_version, change_method,
             evidence_json, features_json, recommended_actions, created_at)
            VALUES
            (:tenant_id, :aoi_id, :year, :week, :pipeline_version, :signal_type, 'OPEN',
             :severity, :confidence, :score, :model_version, :change_method,
             :evidence, :features, :actions, :created_at)
            ON CONFLICT (tenant_id, aoi_id, year, week, pipeline_version, signal_type)
            DO UPDATE SET
              score = EXCLUDED.score,
              evidence_json = EXCLUDED.evidence_json,
              features_json = EXCLUDED.features_json,
              updated_at = now()
            """
        )
        self._db.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "aoi_id": aoi_id,
                "year": year,
                "week": week,
                "pipeline_version": pipeline_version,
                "signal_type": signal_type,
                "severity": severity,
                "confidence": confidence,
                "score": score,
                "model_version": model_version,
                "change_method": change_method,
                "evidence": json.dumps(evidence),
                "features": json.dumps(features),
                "actions": json.dumps(recommended_actions),
                "created_at": created_at,
            },
        )
        self._db.commit()
