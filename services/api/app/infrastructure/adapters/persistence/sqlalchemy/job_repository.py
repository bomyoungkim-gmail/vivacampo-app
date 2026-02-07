"""SQLAlchemy adapter for job repository (domain port)."""
from __future__ import annotations

import json
from typing import List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.job_repository import IJobRepository
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.adapters.persistence.sqlalchemy.base_repository import BaseSQLAlchemyRepository


class SQLAlchemyJobRepository(IJobRepository, BaseSQLAlchemyRepository):
    def __init__(self, db: Session):
        super().__init__(db)

    async def list_jobs(
        self,
        tenant_id: TenantId,
        aoi_id: Optional[UUID] = None,
        job_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        conditions = ["tenant_id = :tenant_id"]
        params = {"tenant_id": str(tenant_id.value), "limit": min(limit, 100)}

        if aoi_id:
            conditions.append("aoi_id = :aoi_id")
            params["aoi_id"] = str(aoi_id)

        if job_type:
            conditions.append("job_type = :job_type")
            params["job_type"] = job_type

        if status:
            conditions.append("status = :status")
            params["status"] = status

        sql = f"""
            SELECT id, aoi_id, job_type, status, created_at, updated_at
            FROM jobs
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT :limit
            """

        return self._execute_query(sql, params)

    async def get_job(self, tenant_id: TenantId, job_id: UUID) -> Optional[dict]:
        sql = """
            SELECT id, aoi_id, job_type, status, payload_json, created_at, updated_at
            FROM jobs
            WHERE id = :job_id AND tenant_id = :tenant_id
            """

        result = self._execute_query(
            sql,
            {"job_id": str(job_id), "tenant_id": str(tenant_id.value)},
            fetch_one=True,
        )

        if not result:
            return None

        payload = json.loads(result["payload_json"]) if result["payload_json"] else None
        return {
            "id": result["id"],
            "aoi_id": result["aoi_id"],
            "job_type": result["job_type"],
            "status": result["status"],
            "payload": payload,
            "created_at": result["created_at"],
            "updated_at": result["updated_at"],
        }

    async def list_runs(self, tenant_id: TenantId, job_id: UUID, limit: int = 10) -> tuple[List[dict], bool]:
        sql_check = "SELECT id FROM jobs WHERE id = :job_id AND tenant_id = :tenant_id"
        exists = self._execute_query(
            sql_check,
            {"job_id": str(job_id), "tenant_id": str(tenant_id.value)},
            fetch_one=True,
        )
        if not exists:
            return [], False

        sql = """
            SELECT id, attempt, status, metrics_json, error_json, started_at, finished_at
            FROM job_runs
            WHERE job_id = :job_id AND tenant_id = :tenant_id
            ORDER BY attempt DESC
            LIMIT :limit
            """

        result = self._execute_query(
            sql,
            {"job_id": str(job_id), "tenant_id": str(tenant_id.value), "limit": limit},
        )
        rows = []
        for row in result:
            rows.append(
                {
                    "id": row["id"],
                    "job_id": job_id,
                    "attempt": row["attempt"],
                    "status": row["status"],
                    "metrics": json.loads(row["metrics_json"]) if row["metrics_json"] else None,
                    "error": json.loads(row["error_json"]) if row["error_json"] else None,
                    "started_at": row["started_at"],
                    "finished_at": row["finished_at"],
                }
            )
        return rows, True

    async def update_status(self, tenant_id: TenantId, job_id: UUID, status: str) -> bool:
        sql = text(
            """
            UPDATE jobs
            SET status = :status, updated_at = now()
            WHERE id = :job_id AND tenant_id = :tenant_id
            """
        )
        result = self.db.execute(
            text(sql),
            {"job_id": str(job_id), "tenant_id": str(tenant_id.value), "status": status},
        )
        self.db.commit()
        return result.rowcount > 0

    async def create_backfill_job(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        job_key: str,
        payload_json: str,
    ) -> UUID:
        sql = text(
            """
            INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
            VALUES (:tenant_id, :aoi_id, 'BACKFILL', :job_key, 'PENDING', :payload)
            ON CONFLICT (tenant_id, job_key) DO UPDATE
            SET status = 'PENDING', updated_at = now()
            RETURNING id
            """
        )
        result = self.db.execute(
            text(sql),
            {
                "tenant_id": str(tenant_id.value),
                "aoi_id": str(aoi_id),
                "job_key": job_key,
                "payload": payload_json,
            },
        )
        self.db.commit()
        return result.fetchone()[0]

    async def create_weather_sync_job(
        self,
        tenant_id: TenantId,
        aoi_id: UUID,
        job_key: str,
        payload_json: str,
    ) -> UUID:
        sql = text(
            """
            INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
            VALUES (:tenant_id, :aoi_id, 'PROCESS_WEATHER', :job_key, 'PENDING', :payload)
            ON CONFLICT (tenant_id, job_key) DO UPDATE
            SET status = 'PENDING', updated_at = now()
            RETURNING id
            """
        )
        result = self.db.execute(
            text(sql),
            {
                "tenant_id": str(tenant_id.value),
                "aoi_id": str(aoi_id),
                "job_key": job_key,
                "payload": payload_json,
            },
        )
        self.db.commit()
        return result.fetchone()[0]

    async def create_job(
        self,
        tenant_id: TenantId,
        aoi_id: Optional[UUID],
        job_type: str,
        job_key: str,
        payload_json: str,
    ) -> UUID:
        sql = text(
            """
            INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
            VALUES (:tenant_id, :aoi_id, :job_type, :job_key, 'PENDING', :payload)
            ON CONFLICT (tenant_id, job_key) DO UPDATE
            SET status = 'PENDING', updated_at = now()
            RETURNING id
            """
        )
        result = self.db.execute(
            text(sql),
            {
                "tenant_id": str(tenant_id.value),
                "aoi_id": str(aoi_id) if aoi_id else None,
                "job_type": job_type,
                "job_key": job_key,
                "payload": payload_json,
            },
        )
        self.db.commit()
        return result.fetchone()[0]

    async def latest_status_by_aois(self, tenant_id: TenantId, aoi_ids: list[UUID]) -> list[dict]:
        if not aoi_ids:
            return []
        sql = """
            SELECT DISTINCT ON (aoi_id)
                aoi_id, status, job_type, updated_at
            FROM jobs
            WHERE tenant_id = :tenant_id
              AND aoi_id = ANY(:aoi_ids)
            ORDER BY aoi_id, updated_at DESC
        """
        rows = self._execute_query(
            sql,
            {
                "tenant_id": str(tenant_id.value),
                "aoi_ids": [str(aoi_id) for aoi_id in aoi_ids],
            },
        )
        return rows
