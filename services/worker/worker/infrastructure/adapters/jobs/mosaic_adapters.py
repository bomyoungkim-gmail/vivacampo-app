"""Adapters for Mosaic creation."""
from __future__ import annotations

import structlog

import planetary_computer
from pystac_client import Client
from sqlalchemy import text
from sqlalchemy.orm import Session

from worker.config import settings
from worker.domain.ports.mosaic_provider import MosaicProvider, MosaicRegistry, MosaicStorage
from worker.shared.aws_clients import S3Client

logger = structlog.get_logger()

PC_STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"


class PlanetaryComputerMosaicProvider(MosaicProvider):
    def __init__(self, stac_url: str = PC_STAC_URL) -> None:
        self._stac_url = stac_url

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
        catalog = Client.open(self._stac_url, modifier=planetary_computer.sign_inplace)
        query = {}
        if collection == "sentinel-2-l2a":
            query["eo:cloud_cover"] = {"lt": max_cloud_cover}
        search = catalog.search(
            collections=[collection],
            bbox=bbox,
            datetime=f"{start_date}/{end_date}",
            query=query if query else None,
            max_items=max_items,
        )
        return search.items()


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
