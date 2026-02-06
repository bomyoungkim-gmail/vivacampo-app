"""SQLAlchemy adapters for AOI geometry and weather persistence."""
from __future__ import annotations

from typing import Iterable

from sqlalchemy import text
from sqlalchemy.orm import Session

from worker.domain.ports.weather_provider import AoiGeometryRepository, WeatherRepository


class SqlAoiGeometryRepository(AoiGeometryRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_geometry(self, *, tenant_id: str, aoi_id: str) -> dict | None:
        row = self._db.execute(
            text("SELECT ST_AsGeoJSON(geom) AS geom_json FROM aois WHERE id = :aoi_id AND tenant_id = :tenant_id"),
            {"aoi_id": aoi_id, "tenant_id": tenant_id},
        ).fetchone()
        if not row or not row.geom_json:
            return None
        return json_loads_safe(row.geom_json)


class SqlWeatherRepository(WeatherRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def save_batch(self, *, tenant_id: str, aoi_id: str, records: Iterable[dict]) -> None:
        records = list(records)
        if not records:
            return

        self._ensure_table()

        sql = text(
            """
            INSERT INTO derived_weather_daily
            (tenant_id, aoi_id, date, temp_max, temp_min, precip_sum, et0_fao)
            VALUES
            (:tenant_id, :aoi_id, :date, :temp_max, :temp_min, :precip_sum, :et0_fao)
            ON CONFLICT (tenant_id, aoi_id, date) DO UPDATE
            SET temp_max = EXCLUDED.temp_max,
                temp_min = EXCLUDED.temp_min,
                precip_sum = EXCLUDED.precip_sum,
                et0_fao = EXCLUDED.et0_fao,
                updated_at = NOW();
            """
        )

        params_list = [
            {
                "tenant_id": tenant_id,
                "aoi_id": aoi_id,
                "date": row["date"],
                "temp_max": row["temp_max"],
                "temp_min": row["temp_min"],
                "precip_sum": row["precip_sum"],
                "et0_fao": row["et0_fao"],
            }
            for row in records
        ]

        self._db.execute(sql, params_list)
        self._db.commit()

    def _ensure_table(self) -> None:
        self._db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS derived_weather_daily (
                    tenant_id UUID NOT NULL,
                    aoi_id UUID NOT NULL,
                    date DATE NOT NULL,
                    temp_max FLOAT,
                    temp_min FLOAT,
                    precip_sum FLOAT,
                    et0_fao FLOAT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (tenant_id, aoi_id, date)
                );
                CREATE INDEX IF NOT EXISTS idx_weather_aoi_date ON derived_weather_daily (aoi_id, date);
                """
            )
        )
        self._db.execute(text("ALTER TABLE derived_weather_daily ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();"))
        self._db.execute(text("ALTER TABLE derived_weather_daily ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();"))
        self._db.commit()


def json_loads_safe(value: str) -> dict:
    import json

    return json.loads(value)
