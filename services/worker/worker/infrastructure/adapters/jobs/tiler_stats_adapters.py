"""Adapters for TiTiler stats and observations persistence."""
from __future__ import annotations

import httpx
from typing import Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from worker.config import settings
from worker.domain.ports.tiler_stats_provider import ObservationsRepository, TilerStatsProvider

HTTP_TIMEOUT = 120.0


class HttpTilerStatsProvider(TilerStatsProvider):
    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or settings.tiler_url

    async def fetch_stats(self, *, mosaic_url: str, expression: str, geometry: dict) -> Optional[Dict[str, float]]:
        url = f"{self._base_url}/mosaic/statistics"
        params = {"url": mosaic_url, "expression": expression}

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.post(url, params=params, json=geometry)

            if response.status_code != 200:
                return None

            data = response.json()
            if "statistics" in data and "b1" in data["statistics"]:
                stats = data["statistics"]["b1"]
                return {
                    "mean": stats.get("mean"),
                    "min": stats.get("min"),
                    "max": stats.get("max"),
                    "std": stats.get("std"),
                    "p10": stats.get("percentile_10"),
                    "p50": stats.get("percentile_50"),
                    "p90": stats.get("percentile_90"),
                    "valid_pixels": stats.get("count"),
                }
        except httpx.TimeoutException:
            return None
        except Exception:
            return None
        return None


class SqlObservationsRepository(ObservationsRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def save_observations(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        year: int,
        week: int,
        stats: Dict[str, Dict[str, float]],
        status: str,
    ) -> None:
        columns = ["tenant_id", "aoi_id", "year", "week", "pipeline_version", "status"]
        values = {
            "tenant_id": tenant_id,
            "aoi_id": aoi_id,
            "year": year,
            "week": week,
            "pipeline_version": "v2-dynamic",
            "status": status,
        }

        stat_mappings = [
            ("ndvi", ["mean", "p10", "p50", "p90", "std"]),
            ("ndwi", ["mean", "std"]),
            ("ndmi", ["mean", "std"]),
            ("evi", ["mean", "std"]),
            ("savi", ["mean", "std"]),
            ("ndre", ["mean", "std"]),
            ("gndvi", ["mean", "std"]),
        ]

        for index_name, stat_fields in stat_mappings:
            if index_name in stats:
                index_stats = stats[index_name]
                for field in stat_fields:
                    col_name = f"{index_name}_{field}"
                    columns.append(col_name)
                    values[col_name] = index_stats.get(field)

        columns_str = ", ".join(columns)
        placeholders = ", ".join(f":{col}" for col in columns)
        update_cols = [c for c in columns if c not in ["tenant_id", "aoi_id", "year", "week", "pipeline_version"]]
        update_str = ", ".join(f"{c} = :{c}" for c in update_cols)

        sql = text(f"""
            INSERT INTO observations_weekly ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT (tenant_id, aoi_id, year, week, pipeline_version)
            DO UPDATE SET {update_str}, updated_at = NOW()
        """)

        self._db.execute(sql, values)
        self._db.commit()
