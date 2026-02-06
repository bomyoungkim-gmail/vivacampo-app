"""Radar adapters for STAC and persistence."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from worker.config import settings
from worker.domain.ports.radar_provider import ObjectStorage, RadarRepository, RadarSceneProvider
from worker.pipeline.stac_client import get_stac_client
from worker.shared.aws_clients import S3Client


class StacRadarProvider(RadarSceneProvider):
    async def search_scenes(
        self,
        aoi_geometry: dict,
        start_date,
        end_date,
        *,
        collections: list[str],
        max_cloud_cover: float,
    ) -> list[dict]:
        client = get_stac_client()
        return await client.search_scenes(
            aoi_geometry,
            start_date,
            end_date,
            max_cloud_cover=max_cloud_cover,
            collections=collections,
        )

    async def download_and_clip_band(self, href: str, geometry: dict, output_path: str) -> None:
        client = get_stac_client()
        await client.download_and_clip_band(href, geometry, output_path)


class S3ObjectStorage(ObjectStorage):
    def __init__(self, client: S3Client | None = None) -> None:
        self._client = client or S3Client()

    def upload_file(self, local_path: str, key: str) -> str:
        return self._client.upload_file(local_path, key)


class SqlRadarRepository(RadarRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def ensure_table(self) -> None:
        sql = text(
            """
            CREATE TABLE IF NOT EXISTS derived_radar_assets (
                tenant_id UUID NOT NULL,
                aoi_id UUID NOT NULL,
                year INTEGER NOT NULL,
                week INTEGER NOT NULL,
                pipeline_version VARCHAR(50) NOT NULL,
                rvi_s3_uri TEXT,
                ratio_s3_uri TEXT,
                vh_s3_uri TEXT,
                vv_s3_uri TEXT,
                rvi_mean FLOAT,
                rvi_std FLOAT,
                ratio_mean FLOAT,
                ratio_std FLOAT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (tenant_id, aoi_id, year, week, pipeline_version)
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
        year: int,
        week: int,
        rvi_uri: str,
        ratio_uri: str,
        vh_uri: str,
        vv_uri: str,
        stats: dict,
    ) -> None:
        self.ensure_table()
        sql = text(
            """
            INSERT INTO derived_radar_assets
            (tenant_id, aoi_id, year, week, pipeline_version,
             rvi_s3_uri, ratio_s3_uri, vh_s3_uri, vv_s3_uri,
             rvi_mean, rvi_std, ratio_mean, ratio_std)
            VALUES
            (:tenant_id, :aoi_id, :year, :week, :pipeline_version,
             :rvi_uri, :ratio_uri, :vh_uri, :vv_uri,
             :rvi_mean, :rvi_std, :ratio_mean, :ratio_std)
            ON CONFLICT (tenant_id, aoi_id, year, week, pipeline_version) DO UPDATE
            SET rvi_s3_uri = :rvi_uri,
                ratio_s3_uri = :ratio_uri,
                vh_s3_uri = :vh_uri,
                vv_s3_uri = :vv_uri,
                rvi_mean = :rvi_mean,
                rvi_std = :rvi_std,
                ratio_mean = :ratio_mean,
                ratio_std = :ratio_std,
                updated_at = NOW();
            """
        )
        self._db.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "aoi_id": aoi_id,
                "year": year,
                "week": week,
                "pipeline_version": settings.pipeline_version,
                "rvi_uri": rvi_uri,
                "ratio_uri": ratio_uri,
                "vh_uri": vh_uri,
                "vv_uri": vv_uri,
                "rvi_mean": stats.get("rvi_mean", 0.0),
                "rvi_std": stats.get("rvi_std", 0.0),
                "ratio_mean": stats.get("ratio_mean", 0.0),
                "ratio_std": stats.get("ratio_std", 0.0),
            },
        )
        self._db.commit()
