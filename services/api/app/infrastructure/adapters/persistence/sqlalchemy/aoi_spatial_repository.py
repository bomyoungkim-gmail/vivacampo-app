"""SQLAlchemy adapter for AOI spatial data (tile metadata and geometry)."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.aoi_spatial_repository import IAoiSpatialRepository
from app.domain.value_objects.tenant_id import TenantId
import structlog

logger = structlog.get_logger()


class SQLAlchemyAoiSpatialRepository(IAoiSpatialRepository):
    def __init__(self, db: Session):
        self.db = db

    async def exists(self, tenant_id: TenantId, aoi_id: UUID) -> bool:
        result = self.db.execute(
            text("SELECT id FROM aois WHERE id = :aoi_id AND tenant_id = :tenant_id"),
            {"aoi_id": str(aoi_id), "tenant_id": str(tenant_id.value)},
        ).fetchone()
        return result is not None

    async def get_tilejson_metadata(self, tenant_id: TenantId, aoi_id: UUID) -> Optional[dict]:
        sql = text(
            """
            SELECT id, name,
                   ST_XMin(geom) as minx, ST_YMin(geom) as miny,
                   ST_XMax(geom) as maxx, ST_YMax(geom) as maxy,
                   ST_X(ST_Centroid(geom)) as cx, ST_Y(ST_Centroid(geom)) as cy
            FROM aois
            WHERE id = :aoi_id AND tenant_id = :tenant_id
            """
        )
        row = self.db.execute(
            sql,
            {"aoi_id": str(aoi_id), "tenant_id": str(tenant_id.value)},
        ).fetchone()
        if not row:
            return None
        return {
            "id": row.id,
            "name": row.name,
            "minx": row.minx,
            "miny": row.miny,
            "maxx": row.maxx,
            "maxy": row.maxy,
            "cx": row.cx,
            "cy": row.cy,
        }

    async def get_geojson(self, tenant_id: TenantId, aoi_id: UUID) -> Optional[dict]:
        sql = text(
            """
            SELECT ST_AsGeoJSON(geom) as geojson
            FROM aois
            WHERE id = :aoi_id AND tenant_id = :tenant_id
            """
        )
        row = self.db.execute(
            sql,
            {"aoi_id": str(aoi_id), "tenant_id": str(tenant_id.value)},
        ).fetchone()
        if not row:
            return None
        try:
            import json

            return json.loads(row.geojson)
        except Exception as exc:
            logger.warning("aoi_geojson_parse_failed", exc_info=exc)
            return None
