"""SQLAlchemy adapters for worker job persistence."""
from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from worker.domain.ports.job_repository import JobRepository, SeasonRepository


class SqlJobRepository(JobRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def mark_status(self, job_id: str, status: str, error_message: Optional[str] = None) -> None:
        sql = text(
            "UPDATE jobs SET status = :status, error_message = :error, updated_at = now() WHERE id = :job_id"
        )
        self._db.execute(sql, {"job_id": job_id, "status": status, "error": error_message})

    def upsert_job(
        self,
        *,
        tenant_id: str,
        aoi_id: str,
        job_type: str,
        job_key: str,
        payload: dict,
    ) -> Optional[str]:
        sql = text(
            """
            INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
            VALUES (:tenant_id, :aoi_id, :job_type, :job_key, 'PENDING', :payload)
            ON CONFLICT (tenant_id, job_key) DO UPDATE
            SET status = 'PENDING', updated_at = now()
            RETURNING id
            """
        )
        result = self._db.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "aoi_id": aoi_id,
                "job_type": job_type,
                "job_key": job_key,
                "payload": json.dumps(payload),
            },
        )
        row = result.fetchone()
        if row:
            return str(row[0])
        return None

    def commit(self) -> None:
        self._db.commit()


class SqlSeasonRepository(SeasonRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def has_season(self, tenant_id: str, aoi_id: str) -> bool:
        sql = text("SELECT id FROM seasons WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id")
        return self._db.execute(sql, {"tenant_id": tenant_id, "aoi_id": aoi_id}).fetchone() is not None
