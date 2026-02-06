"""Adapters for WARM_CACHE."""
from __future__ import annotations

from typing import Optional, Tuple

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from worker.config import settings
from worker.domain.ports.warm_cache_provider import AoiBoundsRepository, TileWarmClient


class SqlAoiBoundsRepository(AoiBoundsRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_bounds(self, *, tenant_id: str, aoi_id: str) -> Optional[Tuple[float, float, float, float]]:
        row = self._db.execute(
            text(
                """
                SELECT
                    ST_XMin(geom) as minx, ST_YMin(geom) as miny,
                    ST_XMax(geom) as maxx, ST_YMax(geom) as maxy
                FROM aois
                WHERE id = :aoi_id AND tenant_id = :tenant_id
                """
            ),
            {"aoi_id": aoi_id, "tenant_id": tenant_id},
        ).fetchone()
        if not row:
            return None
        return row.minx, row.miny, row.maxx, row.maxy


class HttpTileWarmClient(TileWarmClient):
    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        self._base_url = base_url or getattr(settings, "api_url", "http://api:8000")
        self._timeout = timeout

    async def fetch_tile(self, *, aoi_id: str, z: int, x: int, y: int, index: str) -> bool:
        url = f"{self._base_url}/v1/tiles/aois/{aoi_id}/{z}/{x}/{y}.png"
        params = {"index": index}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, params=params, follow_redirects=True)
            return response.status_code in [200, 307]
        except Exception:
            return False
