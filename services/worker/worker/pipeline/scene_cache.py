"""Scene cache repository for STAC metadata."""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


class SceneCacheRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    @staticmethod
    def build_cache_key(
        *,
        provider_name: str,
        collections: List[str],
        start_date: datetime | date,
        end_date: datetime | date,
        max_cloud_cover: float,
        bbox: Optional[List[float]] = None,
        geometry: Optional[Dict[str, Any]] = None,
    ) -> str:
        payload = {
            "provider": provider_name,
            "collections": sorted(collections),
            "start_date": str(start_date),
            "end_date": str(end_date),
            "max_cloud_cover": max_cloud_cover,
            "bbox": bbox,
            "geometry": geometry,
        }
        raw = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def save(
        self,
        *,
        cache_key: str,
        provider_name: str,
        collections: List[str],
        start_date: datetime | date,
        end_date: datetime | date,
        max_cloud_cover: float,
        bbox: Optional[List[float]],
        geometry: Optional[Dict[str, Any]],
        scenes: List[Dict[str, Any]],
    ) -> None:
        sql = text(
            """
            INSERT INTO stac_scene_cache
            (cache_key, provider_name, collections, start_date, end_date, max_cloud_cover, bbox, geometry, scenes)
            VALUES
            (:cache_key, :provider_name, :collections, :start_date, :end_date, :max_cloud_cover, :bbox, :geometry, :scenes)
            ON CONFLICT (cache_key) DO UPDATE
            SET scenes = :scenes,
                updated_at = NOW()
            """
        )
        self._db.execute(
            sql,
            {
                "cache_key": cache_key,
                "provider_name": provider_name,
                "collections": ",".join(sorted(collections)),
                "start_date": start_date,
                "end_date": end_date,
                "max_cloud_cover": max_cloud_cover,
                "bbox": json.dumps(bbox) if bbox else None,
                "geometry": json.dumps(geometry) if geometry else None,
                "scenes": json.dumps(scenes),
            },
        )
        self._db.commit()

    def get(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        sql = text("SELECT scenes FROM stac_scene_cache WHERE cache_key = :cache_key")
        row = self._db.execute(sql, {"cache_key": cache_key}).fetchone()
        if not row:
            return None
        return json.loads(row[0]) if row[0] else None

    def cleanup(self, *, max_age_days: int = 14) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        sql = text("DELETE FROM stac_scene_cache WHERE updated_at < :cutoff")
        result = self._db.execute(sql, {"cutoff": cutoff})
        self._db.commit()
        return result.rowcount
