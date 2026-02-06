"""Adapters for DETECT_HARVEST."""
from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from worker.domain.ports.harvest_provider import HarvestSignalRepository, RadarMetricsRepository


class SqlRadarMetricsRepository(RadarMetricsRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_rvi_mean(self, *, tenant_id: str, aoi_id: str, year: int, week: int) -> float | None:
        sql = text(
            """
            SELECT rvi_mean
            FROM derived_radar_assets
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id AND year = :year AND week = :week
            LIMIT 1
            """
        )
        row = self._db.execute(
            sql,
            {"tenant_id": tenant_id, "aoi_id": aoi_id, "year": year, "week": week},
        ).fetchone()
        return row.rvi_mean if row else None


class SqlHarvestSignalRepository(HarvestSignalRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def create_signal(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
        rvi_current: float,
        rvi_previous: float,
    ) -> None:
        rvi_drop = rvi_previous - rvi_current
        sql = text(
            """
            INSERT INTO opportunity_signals
            (id, tenant_id, aoi_id, year, week, signal_type, status, severity,
             confidence, score, model_version, evidence_json, recommended_actions, created_at)
            VALUES
            (gen_random_uuid(), :tenant_id, :aoi_id, :year, :week, 'HARVEST_DETECTED',
             'NEW', 'INFO', 0.85, :score, 'harvest_v1', :evidence, :actions, NOW())
            ON CONFLICT DO NOTHING
            """
        )
        evidence = json.dumps(
            {
                "rvi_current": rvi_current,
                "rvi_previous": rvi_previous,
                "rvi_drop": rvi_drop,
                "detection_method": "radar_rvi_drop",
            }
        )
        actions = json.dumps(
            [
                "Verificar colheita em campo",
                "Atualizar registro de produtividade",
                "Notificar equipe de logística",
            ]
        )

        self._db.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "aoi_id": aoi_id,
                "year": year,
                "week": week,
                "score": max(0.0, min(rvi_drop, 1.0)),
                "evidence": evidence,
                "actions": actions,
            },
        )
        self._db.commit()
