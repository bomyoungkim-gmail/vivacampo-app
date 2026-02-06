"""SQLAlchemy adapter for AOI repository (domain port)."""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.entities.aoi import AOI
from app.domain.ports.aoi_repository import IAOIRepository
from app.domain.value_objects.area_hectares import AreaHectares
from app.domain.value_objects.geometry_wkt import GeometryWkt
from app.domain.value_objects.tenant_id import TenantId


class SQLAlchemyAOIRepository(IAOIRepository):
    def __init__(self, db: Session):
        self.db = db

    async def create(self, aoi: AOI) -> AOI:
        sql = text(
            """
            INSERT INTO aois (tenant_id, farm_id, name, use_type, geom, area_ha, status)
            VALUES (
                :tenant_id, :farm_id, :name, :use_type,
                ST_GeomFromText(:geom, 4326),
                ST_Area(ST_GeomFromText(:geom, 4326)::geography) / 10000,
                :status
            )
            RETURNING id, farm_id, name, use_type, area_ha, status, created_at, ST_AsText(geom) as geometry
            """
        )

        result = self.db.execute(
            sql,
            {
                "tenant_id": str(aoi.tenant_id.value),
                "farm_id": str(aoi.farm_id),
                "name": aoi.name,
                "use_type": aoi.use_type,
                "geom": aoi.geometry_wkt.value,
                "status": aoi.status,
            },
        )
        self.db.commit()
        row = result.fetchone()

        return AOI(
            id=row.id,
            tenant_id=TenantId(value=aoi.tenant_id.value),
            farm_id=row.farm_id,
            name=row.name,
            use_type=row.use_type,
            status=row.status,
            geometry_wkt=GeometryWkt(value=row.geometry),
            area_hectares=AreaHectares(value=float(row.area_ha)),
            created_at=row.created_at,
        )

    async def get_by_id(self, tenant_id: TenantId, aoi_id: UUID) -> Optional[AOI]:
        sql = text(
            """
            SELECT id, farm_id, name, use_type, area_ha, status, created_at,
                   ST_AsText(geom) as geometry
            FROM aois
            WHERE id = :aoi_id AND tenant_id = :tenant_id
            """
        )
        result = self.db.execute(
            sql,
            {"aoi_id": str(aoi_id), "tenant_id": str(tenant_id.value)},
        ).fetchone()

        if not result:
            return None

        return AOI(
            id=result.id,
            tenant_id=TenantId(value=tenant_id.value),
            farm_id=result.farm_id,
            name=result.name,
            use_type=result.use_type,
            status=result.status,
            geometry_wkt=GeometryWkt(value=result.geometry),
            area_hectares=AreaHectares(value=float(result.area_ha)),
            created_at=result.created_at,
        )

    async def update(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        name: Optional[str] = None,
        use_type: Optional[str] = None,
        status: Optional[str] = None,
        geometry_wkt: Optional[str] = None,
    ) -> Optional[AOI]:
        updates = []
        params = {"aoi_id": str(aoi_id), "tenant_id": str(tenant_id.value)}

        if name is not None:
            updates.append("name = :name")
            params["name"] = name

        if use_type is not None:
            updates.append("use_type = :use_type")
            params["use_type"] = use_type

        if status is not None:
            updates.append("status = :status")
            params["status"] = status

        if geometry_wkt is not None:
            updates.append("geom = ST_GeomFromText(:geom, 4326)")
            updates.append("area_ha = ST_Area(ST_GeomFromText(:geom, 4326)::geography) / 10000")
            params["geom"] = geometry_wkt

        if not updates:
            return None

        sql = text(
            f"""
            UPDATE aois
            SET {', '.join(updates)}
            WHERE id = :aoi_id AND tenant_id = :tenant_id
            RETURNING id, farm_id, name, use_type, area_ha, status, created_at, ST_AsText(geom) as geometry
            """
        )

        result = self.db.execute(sql, params)
        self.db.commit()
        row = result.fetchone()
        if not row:
            return None

        return AOI(
            id=row.id,
            tenant_id=TenantId(value=tenant_id.value),
            farm_id=row.farm_id,
            name=row.name,
            use_type=row.use_type,
            status=row.status,
            geometry_wkt=GeometryWkt(value=row.geometry),
            area_hectares=AreaHectares(value=float(row.area_ha)),
            created_at=row.created_at,
        )

    async def delete(self, tenant_id: TenantId, aoi_id: UUID) -> bool:
        sql = text("DELETE FROM aois WHERE id = :aoi_id AND tenant_id = :tenant_id")
        result = self.db.execute(sql, {"aoi_id": str(aoi_id), "tenant_id": str(tenant_id.value)})
        self.db.commit()
        return result.rowcount > 0

    async def list_by_tenant(
        self,
        tenant_id: TenantId,
        farm_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[AOI]:
        conditions = ["tenant_id = :tenant_id"]
        params = {"tenant_id": str(tenant_id.value), "limit": limit}

        if farm_id:
            conditions.append("farm_id = :farm_id")
            params["farm_id"] = str(farm_id)

        if status:
            conditions.append("status = :status")
            params["status"] = status

        sql = text(
            f"""
            SELECT id, farm_id, name, use_type, area_ha, status, created_at,
                   ST_AsText(geom) as geometry
            FROM aois
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT :limit
            """
        )

        result = self.db.execute(sql, params)
        aois: List[AOI] = []
        for row in result:
            aois.append(
                AOI(
                    id=row.id,
                    tenant_id=TenantId(value=tenant_id.value),
                    farm_id=row.farm_id,
                    name=row.name,
                    use_type=row.use_type,
                    status=row.status,
                    geometry_wkt=GeometryWkt(value=row.geometry),
                    area_hectares=AreaHectares(value=float(row.area_ha)),
                    created_at=row.created_at,
                )
            )
        return aois
