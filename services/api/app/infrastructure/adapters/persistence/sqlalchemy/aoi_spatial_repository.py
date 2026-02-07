"""SQLAlchemy adapter for AOI spatial data (tile metadata and geometry)."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.ports.aoi_spatial_repository import IAoiSpatialRepository
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.adapters.persistence.sqlalchemy.base_repository import BaseSQLAlchemyRepository
import structlog

logger = structlog.get_logger()


class SQLAlchemyAoiSpatialRepository(IAoiSpatialRepository, BaseSQLAlchemyRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    async def exists(self, tenant_id: TenantId, aoi_id: UUID) -> bool:
        result = self._execute_query(
            "SELECT id FROM aois WHERE id = :aoi_id AND tenant_id = :tenant_id",
            {"aoi_id": str(aoi_id), "tenant_id": str(tenant_id.value)},
            fetch_one=True,
        )
        return result is not None

    async def get_tilejson_metadata(self, tenant_id: TenantId, aoi_id: UUID) -> Optional[dict]:
        sql = """
            SELECT id, name,
                   ST_XMin(geom) as minx, ST_YMin(geom) as miny,
                   ST_XMax(geom) as maxx, ST_YMax(geom) as maxy,
                   ST_X(ST_Centroid(geom)) as cx, ST_Y(ST_Centroid(geom)) as cy
            FROM aois
            WHERE id = :aoi_id AND tenant_id = :tenant_id
            """
        row = self._execute_query(
            sql,
            {"aoi_id": str(aoi_id), "tenant_id": str(tenant_id.value)},
            fetch_one=True,
        )
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "minx": row["minx"],
            "miny": row["miny"],
            "maxx": row["maxx"],
            "maxy": row["maxy"],
            "cx": row["cx"],
            "cy": row["cy"],
        }

    async def get_geojson(self, tenant_id: TenantId, aoi_id: UUID) -> Optional[dict]:
        sql = """
            SELECT ST_AsGeoJSON(geom) as geojson
            FROM aois
            WHERE id = :aoi_id AND tenant_id = :tenant_id
            """
        row = self._execute_query(
            sql,
            {"aoi_id": str(aoi_id), "tenant_id": str(tenant_id.value)},
            fetch_one=True,
        )
        if not row:
            return None
        try:
            import json

            return json.loads(row["geojson"])
        except Exception as exc:
            logger.warning("aoi_geojson_parse_failed", exc_info=exc)
            return None

    async def simulate_split(
        self,
        tenant_id: TenantId,
        geometry_wkt: str,
        mode: str,
        target_count: int,
    ) -> list[dict]:
        if target_count <= 0:
            raise ValueError("target_count must be >= 1")
        if mode not in {"voronoi", "grid"}:
            raise ValueError("mode must be 'voronoi' or 'grid'")

        if mode == "voronoi":
            sql = """
                WITH input AS (
                    SELECT ST_GeomFromText(:geom, 4326) AS geom
                ),
                geom_3857 AS (
                    SELECT ST_Transform(geom, 3857) AS geom FROM input
                ),
                points AS (
                    SELECT ST_GeneratePoints(geom, :target_count) AS pts FROM geom_3857
                ),
                cells AS (
                    SELECT (ST_Dump(ST_VoronoiPolygons(pts))).geom AS geom FROM points
                ),
                clipped AS (
                    SELECT ST_Intersection(c.geom, g.geom) AS geom
                    FROM cells c CROSS JOIN geom_3857 g
                ),
                polys AS (
                    SELECT ST_Multi(ST_CollectionExtract(geom, 3)) AS geom
                    FROM clipped
                    WHERE geom IS NOT NULL AND NOT ST_IsEmpty(geom)
                ),
                back_4326 AS (
                    SELECT ST_Transform(geom, 4326) AS geom FROM polys
                )
                SELECT
                    ST_AsText(geom) AS geometry_wkt,
                    ST_Area(geom::geography) / 10000 AS area_ha
                FROM back_4326
            """
        else:
            sql = """
                WITH input AS (
                    SELECT ST_GeomFromText(:geom, 4326) AS geom
                ),
                geom_3857 AS (
                    SELECT ST_Transform(geom, 3857) AS geom FROM input
                ),
                params AS (
                    SELECT
                        ST_Area(geom) AS area_m2,
                        geom
                    FROM geom_3857
                ),
                grid AS (
                    SELECT (ST_Dump(ST_SquareGrid(
                        sqrt(area_m2 / NULLIF(:target_count, 0)),
                        geom
                    ))).geom AS geom
                    FROM params
                ),
                clipped AS (
                    SELECT ST_Intersection(g.geom, p.geom) AS geom
                    FROM grid g CROSS JOIN params p
                ),
                polys AS (
                    SELECT ST_Multi(ST_CollectionExtract(geom, 3)) AS geom
                    FROM clipped
                    WHERE geom IS NOT NULL AND NOT ST_IsEmpty(geom)
                ),
                back_4326 AS (
                    SELECT ST_Transform(geom, 4326) AS geom FROM polys
                )
                SELECT
                    ST_AsText(geom) AS geometry_wkt,
                    ST_Area(geom::geography) / 10000 AS area_ha
                FROM back_4326
            """

        rows = self._execute_query(
            sql,
            {"geom": geometry_wkt, "target_count": target_count},
        )
        return [
            {"geometry_wkt": row["geometry_wkt"], "area_ha": float(row["area_ha"])}
            for row in rows
        ]
