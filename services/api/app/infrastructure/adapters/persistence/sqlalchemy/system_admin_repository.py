"""SQLAlchemy adapter for system admin operations."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.system_admin_repository import ISystemAdminRepository


class SQLAlchemySystemAdminRepository(ISystemAdminRepository):
    def __init__(self, db: Session):
        self.db = db

    async def list_tenants(self, tenant_type: Optional[str], limit: int) -> list[dict]:
        conditions = []
        params = {"limit": min(limit, 100)}
        if tenant_type:
            conditions.append("type = :tenant_type")
            params["tenant_type"] = tenant_type

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = text(
            f"""
            SELECT id, name, type, status, created_at
            FROM tenants
            {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit
            """
        )
        result = self.db.execute(sql, params)
        return [dict(row._mapping) for row in result]

    async def create_tenant(self, name: str, tenant_type: str) -> dict:
        sql = text(
            """
            INSERT INTO tenants (name, type, status)
            VALUES (:name, :type, 'ACTIVE')
            RETURNING id, name, type, status, created_at
            """
        )
        result = self.db.execute(sql, {"name": name, "type": tenant_type})
        self.db.commit()
        row = result.fetchone()
        return dict(row._mapping)

    async def get_tenant_status(self, tenant_id: UUID) -> Optional[str]:
        sql = text("SELECT status FROM tenants WHERE id = :tenant_id")
        row = self.db.execute(sql, {"tenant_id": str(tenant_id)}).fetchone()
        return row.status if row else None

    async def update_tenant_status(self, tenant_id: UUID, status: str) -> bool:
        sql = text(
            """
            UPDATE tenants
            SET status = :status
            WHERE id = :tenant_id
            """
        )
        result = self.db.execute(sql, {"status": status, "tenant_id": str(tenant_id)})
        self.db.commit()
        return result.rowcount > 0

    async def list_jobs(self, status: Optional[str], job_type: Optional[str], limit: int) -> list[dict]:
        conditions = []
        params = {"limit": min(limit, 200)}
        if status:
            conditions.append("j.status = :status")
            params["status"] = status
        if job_type:
            conditions.append("j.job_type = :job_type")
            params["job_type"] = job_type

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = text(
            f"""
            SELECT 
                j.id, j.tenant_id, j.aoi_id, j.job_type, j.job_key, j.status, j.error_message, j.created_at, j.updated_at,
                a.name as aoi_name, f.name as farm_name
            FROM jobs j
            LEFT JOIN aois a ON a.id = j.aoi_id
            LEFT JOIN farms f ON f.id = a.farm_id
            {where_clause}
            ORDER BY j.created_at DESC
            LIMIT :limit
            """
        )
        result = self.db.execute(sql, params)
        return [dict(row._mapping) for row in result]

    async def retry_job(self, job_id: UUID) -> bool:
        sql = text(
            """
            UPDATE jobs
            SET status = 'PENDING', updated_at = now()
            WHERE id = :job_id AND status IN ('FAILED', 'CANCELLED')
            """
        )
        result = self.db.execute(sql, {"job_id": str(job_id)})
        self.db.commit()
        return result.rowcount > 0

    async def list_missing_aois(self, limit: int) -> list[dict]:
        sql = text(
            """
            SELECT a.id, a.tenant_id
            FROM aois a
            WHERE a.status = 'ACTIVE'
              AND NOT EXISTS (
                  SELECT 1 FROM derived_assets d
                  WHERE d.tenant_id = a.tenant_id AND d.aoi_id = a.id
              )
            LIMIT :limit
            """
        )
        rows = self.db.execute(sql, {"limit": min(limit, 500)}).fetchall()
        return [dict(row._mapping) for row in rows]

    async def list_active_aois(self, limit: int) -> list[dict]:
        sql = text(
            """
            SELECT a.id, a.tenant_id, a.name as aoi_name, f.name as farm_name
            FROM aois a
            LEFT JOIN farms f ON f.id = a.farm_id
            WHERE a.status = 'ACTIVE'
            ORDER BY a.created_at DESC
            LIMIT :limit
            """
        )
        rows = self.db.execute(sql, {"limit": limit}).fetchall()
        return [dict(row._mapping) for row in rows]

    async def list_observation_weeks(self, tenant_id: UUID, aoi_id: UUID) -> list[tuple[int, int]]:
        sql = text(
            """
            SELECT year, week
            FROM observations_weekly
            WHERE tenant_id = :tenant_id
              AND aoi_id = :aoi_id
            """
        )
        rows = self.db.execute(
            sql,
            {"tenant_id": str(tenant_id), "aoi_id": str(aoi_id)},
        ).fetchall()
        return [(row.year, row.week) for row in rows]

    async def get_job_stats_24h(self) -> dict:
        sql = text(
            """
            SELECT 
                COUNT(*) FILTER (WHERE status = 'PENDING') as pending,
                COUNT(*) FILTER (WHERE status = 'RUNNING') as running,
                COUNT(*) FILTER (WHERE status = 'FAILED') as failed
            FROM jobs
            WHERE created_at > now() - interval '24 hours'
            """
        )
        stats = self.db.execute(sql).fetchone()
        return {
            "pending": stats.pending,
            "running": stats.running,
            "failed": stats.failed,
        }

    async def get_queue_stats(self) -> dict:
        sql = text(
            """
            SELECT job_type, status, COUNT(*) as count
            FROM jobs
            WHERE created_at > now() - interval '7 days'
            GROUP BY job_type, status
            ORDER BY job_type, status
            """
        )
        result = self.db.execute(sql)
        stats = {}
        for row in result:
            stats.setdefault(row.job_type, {})[row.status] = row.count
        return stats

    async def list_audit_logs(self, limit: int) -> list[dict]:
        sql = text(
            """
            SELECT tenant_id, action, resource_type, resource_id, 
                   changes_json, metadata_json, created_at
            FROM audit_log
            ORDER BY created_at DESC
            LIMIT :limit
            """
        )
        result = self.db.execute(sql, {"limit": min(limit, 200)})
        return [dict(row._mapping) for row in result]

    async def check_db(self) -> tuple[bool, str | None]:
        try:
            self.db.execute(text("SELECT 1"))
            return True, None
        except Exception as exc:
            return False, str(exc)
