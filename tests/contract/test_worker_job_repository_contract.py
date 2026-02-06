import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[2]
WORKER_PATH = ROOT / "services" / "worker"
if str(WORKER_PATH) not in sys.path:
    sys.path.insert(0, str(WORKER_PATH))


@pytest.mark.integration
def test_sql_job_repository_contract():
    from worker.database import SessionLocal
    from worker.infrastructure.adapters.jobs.sql_job_repository import SqlJobRepository

    session = SessionLocal()
    try:
        tenant_id = str(uuid.uuid4())
        farm_id = str(uuid.uuid4())
        aoi_id = str(uuid.uuid4())

        session.execute(
            text("""
                INSERT INTO tenants (id, type, name, status, plan, quotas)
                VALUES (:id, 'COMPANY', 'Contract Tenant', 'ACTIVE', 'BASIC', '{}'::jsonb)
            """),
            {"id": tenant_id},
        )
        session.execute(
            text("""
                INSERT INTO farms (id, tenant_id, name, timezone)
                VALUES (:id, :tenant_id, 'Contract Farm', 'America/Sao_Paulo')
            """),
            {"id": farm_id, "tenant_id": tenant_id},
        )
        session.execute(
            text("""
                INSERT INTO aois (id, tenant_id, farm_id, name, use_type, status, geom, area_ha)
                VALUES (
                    :id, :tenant_id, :farm_id, 'Contract AOI', 'CROP', 'ACTIVE',
                    ST_GeomFromText(:geom, 4326), :area_ha
                )
            """),
            {
                "id": aoi_id,
                "tenant_id": tenant_id,
                "farm_id": farm_id,
                "geom": "MULTIPOLYGON(((-47.0 -23.0, -47.0 -23.1, -47.1 -23.1, -47.1 -23.0, -47.0 -23.0)))",
                "area_ha": 12.0,
            },
        )
        session.commit()

        repo = SqlJobRepository(session)
        job_key = f"contract-{uuid.uuid4().hex}"
        job_id = repo.upsert_job(
            tenant_id=tenant_id,
            aoi_id=aoi_id,
            job_type="PROCESS_WEEK",
            job_key=job_key,
            payload={"tenant_id": tenant_id, "aoi_id": aoi_id, "year": 2024, "week": 1},
        )
        repo.commit()
        assert job_id is not None

        job_id2 = repo.upsert_job(
            tenant_id=tenant_id,
            aoi_id=aoi_id,
            job_type="PROCESS_WEEK",
            job_key=job_key,
            payload={"tenant_id": tenant_id, "aoi_id": aoi_id, "year": 2024, "week": 1},
        )
        repo.commit()
        assert job_id2 == job_id

        repo.mark_status(job_id, "RUNNING")
        repo.commit()
        status = session.execute(
            text("SELECT status FROM jobs WHERE id = :job_id"),
            {"job_id": job_id},
        ).scalar_one()
        assert status == "RUNNING"
    finally:
        session.execute(text("DELETE FROM tenants WHERE id = :tenant_id"), {"tenant_id": tenant_id})
        session.commit()
        session.close()
