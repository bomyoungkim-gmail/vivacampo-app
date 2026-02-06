"""Topography adapters."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from worker.config import settings
from worker.domain.ports.topography_provider import TopographyRepository, TopographySceneProvider
from worker.pipeline.stac_client import get_stac_client


class StacTopographyProvider(TopographySceneProvider):
    async def search_scenes(
        self,
        aoi_geometry: dict,
        start_date: datetime,
        end_date: datetime,
        *,
        collections: list[str],
    ) -> list[dict]:
        client = get_stac_client()
        return await client.search_scenes(
            aoi_geometry,
            start_date,
            end_date,
            collections=collections,
        )

    async def download_and_clip_band(self, href: str, geometry: dict, output_path: str) -> None:
        client = get_stac_client()
        await client.download_and_clip_band(href, geometry, output_path)


class SqlTopographyRepository(TopographyRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def ensure_table(self) -> None:
        sql = text(
            """
            CREATE TABLE IF NOT EXISTS derived_topography (
                tenant_id UUID NOT NULL,
                aoi_id UUID NOT NULL,
                pipeline_version VARCHAR(50) NOT NULL,
                dem_s3_uri TEXT,
                slope_s3_uri TEXT,
                aspect_s3_uri TEXT,
                elevation_min FLOAT,
                elevation_max FLOAT,
                elevation_mean FLOAT,
                slope_mean FLOAT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (tenant_id, aoi_id, pipeline_version)
            );
            """
        )
        self._db.execute(sql)
        self._db.commit()

    def save_assets(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        dem_uri: str,
        slope_uri: str,
        aspect_uri: str | None,
        stats: dict,
    ) -> None:
        self.ensure_table()
        sql = text(
            """
            INSERT INTO derived_topography
            (tenant_id, aoi_id, pipeline_version,
             dem_s3_uri, slope_s3_uri, aspect_s3_uri,
             elevation_min, elevation_max, elevation_mean, slope_mean)
            VALUES
            (:tenant_id, :aoi_id, :pipeline_version,
             :dem_uri, :slope_uri, :aspect_uri,
             :ele_min, :ele_max, :ele_mean, :slope_mean)
            ON CONFLICT (tenant_id, aoi_id, pipeline_version) DO UPDATE
            SET dem_s3_uri = :dem_uri,
                slope_s3_uri = :slope_uri,
                aspect_s3_uri = :aspect_uri,
                elevation_min = :ele_min,
                elevation_max = :ele_max,
                elevation_mean = :ele_mean,
                slope_mean = :slope_mean,
                updated_at = NOW();
            """
        )
        self._db.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "aoi_id": aoi_id,
                "pipeline_version": settings.pipeline_version,
                "dem_uri": dem_uri,
                "slope_uri": slope_uri,
                "aspect_uri": aspect_uri,
                "ele_min": stats.get("ele_min", 0.0),
                "ele_max": stats.get("ele_max", 0.0),
                "ele_mean": stats.get("ele_mean", 0.0),
                "slope_mean": stats.get("slope_mean", 0.0),
            },
        )
        self._db.commit()
