"""Adapters for Mosaic creation."""
from __future__ import annotations

import structlog

import asyncio
from sqlalchemy import text
from sqlalchemy.orm import Session

from worker.config import settings
from worker.domain.ports.mosaic_provider import MosaicProvider, MosaicRegistry, MosaicStorage
from worker.shared.aws_clients import S3Client
from worker.pipeline.providers.registry import get_satellite_provider

logger = structlog.get_logger()

class PlanetaryComputerMosaicProvider(MosaicProvider):
    def search_scenes(
        self,
        *,
        collection: str,
        start_date: str,
        end_date: str,
        bbox: list[float],
        max_cloud_cover: float,
        max_items: int,
    ):
        provider = get_satellite_provider()
        return asyncio.run(
            provider.search_raw_items(
                bbox=bbox,
                start_date=start_date,
                end_date=end_date,
                max_cloud_cover=max_cloud_cover,
                collections=[collection],
                max_items=max_items,
            )
        )


class S3MosaicStorage(MosaicStorage):
    def __init__(self, client: S3Client | None = None) -> None:
        self._client = client or S3Client()

    def save_json(self, *, key: str, payload: dict) -> str:
        self._client.upload_json(key, payload)
        return f"s3://{settings.s3_bucket}/{key}"

    def exists(self, *, key: str) -> bool:
        return self._client.object_exists(key)


class SqlMosaicRegistry(MosaicRegistry):
    def __init__(self, db: Session) -> None:
        self._db = db

    def save_record(self, *, collection: str, year: int, week: int, url: str, scene_count: int) -> None:
        try:
            sql = text(
                """
                INSERT INTO mosaic_registry (collection, year, week, s3_url, scene_count, created_at)
                VALUES (:collection, :year, :week, :s3_url, :scene_count, NOW())
                ON CONFLICT (collection, year, week)
                DO UPDATE SET s3_url = :s3_url, scene_count = :scene_count, updated_at = NOW()
                """
            )
            self._db.execute(
                sql,
                {
                    "collection": collection,
                    "year": year,
                    "week": week,
                    "s3_url": url,
                    "scene_count": scene_count,
                },
            )
            self._db.commit()
        except Exception as exc:
            logger.warning("mosaic_registry_save_failed", error=str(exc))
            self._db.rollback()
