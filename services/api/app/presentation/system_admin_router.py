from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import date, datetime, timedelta
from uuid import UUID
from app.database import get_db
from app.auth.dependencies import get_current_system_admin
from app.schemas import TenantView, TenantCreate, TenantPatch, SystemJobView, DLQMessageView
from app.domain.audit import get_audit_logger
import structlog
import json

logger = structlog.get_logger()
router = APIRouter()


def _iso_week_start(year: int, week: int) -> date:
    return date.fromisocalendar(year, week, 1)


def _iso_week_end(year: int, week: int) -> date:
    return date.fromisocalendar(year, week, 7)


@router.get("/admin/tenants", response_model=List[TenantView])
async def list_tenants(
    tenant_type: Optional[str] = None,
    limit: int = 50,
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    List all tenants (SYSTEM_ADMIN only).
    """
    conditions = []
    params = {"limit": min(limit, 100)}
    
    if tenant_type:
        conditions.append("type = :tenant_type")
        params["tenant_type"] = tenant_type
    
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    sql = text(f"""
        SELECT id, name, type, status, created_at
        FROM tenants
        {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    
    result = db.execute(sql, params)
    
    tenants = []
    for row in result:
        tenants.append(TenantView(
            id=row.id,
            name=row.name,
            type=row.type,
            status=row.status,
            created_at=row.created_at
        ))
    
    return tenants


@router.post("/admin/tenants", response_model=TenantView, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new tenant (SYSTEM_ADMIN only).
    """
    sql = text("""
        INSERT INTO tenants (name, type, status)
        VALUES (:name, :type, 'ACTIVE')
        RETURNING id, name, type, status, created_at
    """)
    
    result = db.execute(sql, {
        "name": tenant_data.name,
        "type": tenant_data.type
    })
    db.commit()
    
    row = result.fetchone()
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log(
        tenant_id="SYSTEM",
        actor_membership_id=None,
        action="CREATE_TENANT",
        resource_type="tenant",
        resource_id=str(row.id),
        metadata={"name": tenant_data.name, "type": tenant_data.type}
    )
    
    return TenantView(
        id=row.id,
        name=row.name,
        type=row.type,
        status=row.status,
        created_at=row.created_at
    )


@router.patch("/admin/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: UUID,
    tenant_patch: TenantPatch,
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    Update tenant (SYSTEM_ADMIN only).
    Can change status (ACTIVE/SUSPENDED).
    """
    # Get current tenant
    sql = text("SELECT status FROM tenants WHERE id = :tenant_id")
    result = db.execute(sql, {"tenant_id": str(tenant_id)}).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    old_status = result.status
    
    # Update status
    sql = text("""
        UPDATE tenants
        SET status = :status
        WHERE id = :tenant_id
    """)
    
    db.execute(sql, {
        "status": tenant_patch.status,
        "tenant_id": str(tenant_id)
    })
    db.commit()
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log(
        tenant_id="SYSTEM",
        actor_membership_id=None,
        action="UPDATE_TENANT",
        resource_type="tenant",
        resource_id=str(tenant_id),
        changes={"status": {"before": old_status, "after": tenant_patch.status}}
    )
    
    return {"message": "Tenant updated", "new_status": tenant_patch.status}


@router.get("/admin/jobs", response_model=List[SystemJobView])
async def list_all_jobs(
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = 100,
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    List all jobs across all tenants (SYSTEM_ADMIN only).
    """
    conditions = []
    params = {"limit": min(limit, 200)}
    
    if status:
        conditions.append("j.status = :status")
        params["status"] = status
    
    if job_type:
        conditions.append("j.job_type = :job_type")
        params["job_type"] = job_type
    
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    sql = text(f"""
        SELECT 
            j.id, j.tenant_id, j.aoi_id, j.job_type, j.job_key, j.status, j.error_message, j.created_at, j.updated_at,
            a.name as aoi_name, f.name as farm_name
        FROM jobs j
        LEFT JOIN aois a ON a.id = j.aoi_id
        LEFT JOIN farms f ON f.id = a.farm_id
        {where_clause}
        ORDER BY j.created_at DESC
        LIMIT :limit
    """)
    
    result = db.execute(sql, params)
    
    jobs = []
    for row in result:
        jobs.append(SystemJobView(
            id=row.id,
            tenant_id=row.tenant_id,
            aoi_id=row.aoi_id,
            aoi_name=row.aoi_name,
            farm_name=row.farm_name,
            job_type=row.job_type,
            job_key=row.job_key,
            status=row.status,
            error_message=row.error_message,
            created_at=row.created_at,
            updated_at=row.updated_at
        ))
    
    return jobs


@router.post("/admin/jobs/{job_id}/retry")
async def admin_retry_job(
    job_id: UUID,
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    Retry any job (SYSTEM_ADMIN only).
    """
    sql = text("""
        UPDATE jobs
        SET status = 'PENDING', updated_at = now()
        WHERE id = :job_id AND status IN ('FAILED', 'CANCELLED')
    """)
    
    result = db.execute(sql, {"job_id": str(job_id)})
    db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Job not found or cannot be retried")
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log(
        tenant_id="SYSTEM",
        actor_membership_id=None,
        action="ADMIN_RETRY_JOB",
        resource_type="job",
        resource_id=str(job_id)
    )
    
    return {"message": "Job retry requested"}


@router.post("/admin/ops/reprocess-missing-aois")
async def reprocess_missing_aois(
    days: int = 56,
    limit: int = 200,
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    Enqueue BACKFILL jobs for AOIs with no derived assets.
    """
    from app.config import settings
    from app.infrastructure.sqs_client import get_sqs_client
    import json
    import hashlib

    to_date = date.today().isoformat()
    from_date = (date.today() - timedelta(days=days)).isoformat()

    sql = text("""
        SELECT a.id, a.tenant_id
        FROM aois a
        WHERE a.status = 'ACTIVE'
          AND NOT EXISTS (
              SELECT 1 FROM derived_assets d
              WHERE d.tenant_id = a.tenant_id AND d.aoi_id = a.id
          )
        LIMIT :limit
    """)

    rows = db.execute(sql, {"limit": min(limit, 500)}).fetchall()
    if not rows:
        return {"queued": 0, "message": "No missing AOIs found"}

    sqs = get_sqs_client()
    queued = 0

    for row in rows:
        job_key = hashlib.sha256(
            f"{row.tenant_id}{row.id}{from_date}{to_date}BACKFILL{settings.pipeline_version}".encode()
        ).hexdigest()

        payload = {
            "tenant_id": str(row.tenant_id),
            "aoi_id": str(row.id),
            "from_date": from_date,
            "to_date": to_date,
            "cadence": "weekly"
        }

        sql_insert = text("""
            INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
            VALUES (:tenant_id, :aoi_id, 'BACKFILL', :job_key, 'PENDING', :payload)
            ON CONFLICT (tenant_id, job_key) DO UPDATE
            SET status = 'PENDING', updated_at = now()
            RETURNING id
        """)

        result = db.execute(sql_insert, {
            "tenant_id": str(row.tenant_id),
            "aoi_id": str(row.id),
            "job_key": job_key,
            "payload": json.dumps(payload)
        })
        db.commit()

        job_id = result.fetchone()[0]

        sqs.send_message(
            settings.sqs_queue_name,
            json.dumps({
                "job_id": str(job_id),
                "job_type": "BACKFILL",
                "payload": payload
            })
        )
        queued += 1

    audit = get_audit_logger(db)
    audit.log(
        tenant_id="SYSTEM",
        actor_membership_id=None,
        action="ADMIN_REPROCESS_MISSING_AOIS",
        resource_type="aoi",
        resource_id=None,
        metadata={"queued": queued, "from_date": from_date, "to_date": to_date}
    )

    return {"queued": queued, "from_date": from_date, "to_date": to_date}


@router.get("/admin/ops/missing-weeks")
async def list_missing_weeks(
    weeks: int = 12,
    limit: int = 50,
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    List missing weekly observations for active AOIs in the last N weeks.
    """
    weeks = max(1, min(weeks, 104))
    limit = max(1, min(limit, 200))

    today = date.today()
    start = today - timedelta(weeks=weeks - 1)

    expected_weeks = []
    cursor = start
    while cursor <= today:
        iso = cursor.isocalendar()
        expected_weeks.append((iso.year, iso.week))
        cursor += timedelta(days=7)

    sql_aois = text("""
        SELECT a.id, a.tenant_id, a.name as aoi_name, f.name as farm_name
        FROM aois a
        LEFT JOIN farms f ON f.id = a.farm_id
        WHERE a.status = 'ACTIVE'
        ORDER BY a.created_at DESC
        LIMIT :limit
    """)

    aois = db.execute(sql_aois, {"limit": limit}).fetchall()
    results = []

    for row in aois:
        sql_obs = text("""
            SELECT year, week
            FROM observations_weekly
            WHERE tenant_id = :tenant_id
              AND aoi_id = :aoi_id
        """)
        existing = db.execute(sql_obs, {
            "tenant_id": row.tenant_id,
            "aoi_id": row.id
        }).fetchall()

        existing_set = {(r.year, r.week) for r in existing}
        missing = [(y, w) for (y, w) in expected_weeks if (y, w) not in existing_set]

        if missing:
            results.append({
                "tenant_id": str(row.tenant_id),
                "aoi_id": str(row.id),
                "farm_name": row.farm_name,
                "aoi_name": row.aoi_name,
                "missing_weeks": missing,
                "missing_count": len(missing)
            })

    return {"weeks": weeks, "items": results}


@router.post("/admin/ops/reprocess-missing-weeks")
async def reprocess_missing_weeks(
    weeks: int = 12,
    limit: int = 50,
    max_runs_per_aoi: int = 3,
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    Enqueue BACKFILL jobs for missing weekly observations in the last N weeks.
    """
    from app.config import settings
    from app.infrastructure.sqs_client import get_sqs_client
    import json
    import hashlib

    weeks = max(1, min(weeks, 104))
    limit = max(1, min(limit, 200))
    max_runs_per_aoi = max(1, min(max_runs_per_aoi, 6))

    today = date.today()
    start = today - timedelta(weeks=weeks - 1)

    expected_weeks = []
    cursor = start
    while cursor <= today:
        iso = cursor.isocalendar()
        expected_weeks.append((iso.year, iso.week))
        cursor += timedelta(days=7)

    sql_aois = text("""
        SELECT a.id, a.tenant_id
        FROM aois a
        WHERE a.status = 'ACTIVE'
        ORDER BY a.created_at DESC
        LIMIT :limit
    """)
    aois = db.execute(sql_aois, {"limit": limit}).fetchall()
    sqs = get_sqs_client()

    queued = 0

    for row in aois:
        sql_obs = text("""
            SELECT year, week
            FROM observations_weekly
            WHERE tenant_id = :tenant_id
              AND aoi_id = :aoi_id
        """)
        existing = db.execute(sql_obs, {
            "tenant_id": row.tenant_id,
            "aoi_id": row.id
        }).fetchall()

        existing_set = {(r.year, r.week) for r in existing}
        missing = [(y, w) for (y, w) in expected_weeks if (y, w) not in existing_set]

        if not missing:
            continue

        # Build contiguous runs
        runs = []
        current = [missing[0]]
        for (y, w) in missing[1:]:
            prev_y, prev_w = current[-1]
            prev_end = _iso_week_end(prev_y, prev_w)
            this_start = _iso_week_start(y, w)
            if this_start == prev_end + timedelta(days=1):
                current.append((y, w))
            else:
                runs.append(current)
                current = [(y, w)]
        runs.append(current)

        for run in runs[:max_runs_per_aoi]:
            from_date = _iso_week_start(run[0][0], run[0][1]).isoformat()
            to_date = _iso_week_end(run[-1][0], run[-1][1]).isoformat()

            job_key = hashlib.sha256(
                f"{row.tenant_id}{row.id}{from_date}{to_date}BACKFILL{settings.pipeline_version}".encode()
            ).hexdigest()

            payload = {
                "tenant_id": str(row.tenant_id),
                "aoi_id": str(row.id),
                "from_date": from_date,
                "to_date": to_date,
                "cadence": "weekly"
            }

            sql_insert = text("""
                INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
                VALUES (:tenant_id, :aoi_id, 'BACKFILL', :job_key, 'PENDING', :payload)
                ON CONFLICT (tenant_id, job_key) DO UPDATE
                SET status = 'PENDING', updated_at = now()
                RETURNING id
            """)

            result = db.execute(sql_insert, {
                "tenant_id": str(row.tenant_id),
                "aoi_id": str(row.id),
                "job_key": job_key,
                "payload": json.dumps(payload)
            })
            db.commit()

            job_id = result.fetchone()[0]
            sqs.send_message(
                settings.sqs_queue_name,
                json.dumps({
                    "job_id": str(job_id),
                    "job_type": "BACKFILL",
                    "payload": payload
                })
            )
            queued += 1

    audit = get_audit_logger(db)
    audit.log(
        tenant_id="SYSTEM",
        actor_membership_id=None,
        action="ADMIN_REPROCESS_MISSING_WEEKS",
        resource_type="aoi",
        resource_id=None,
        metadata={"weeks": weeks, "limit": limit, "queued": queued}
    )

    return {"queued": queued, "weeks": weeks, "limit": limit}


@router.get("/admin/ops/health")
async def system_health(
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    System-wide health check (SYSTEM_ADMIN only).
    """
    # Check database
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check job queue stats
    sql = text("""
        SELECT 
            COUNT(*) FILTER (WHERE status = 'PENDING') as pending,
            COUNT(*) FILTER (WHERE status = 'RUNNING') as running,
            COUNT(*) FILTER (WHERE status = 'FAILED') as failed
        FROM jobs
        WHERE created_at > now() - interval '24 hours'
    """)
    
    stats = db.execute(sql).fetchone()
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "jobs_24h": {
            "pending": stats.pending,
            "running": stats.running,
            "failed": stats.failed
        }
    }


@router.get("/admin/ops/queues")
async def queue_stats(
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    Queue statistics (SYSTEM_ADMIN only).
    """
    sql = text("""
        SELECT job_type, status, COUNT(*) as count
        FROM jobs
        WHERE created_at > now() - interval '7 days'
        GROUP BY job_type, status
        ORDER BY job_type, status
    """)
    
    result = db.execute(sql)
    
    stats = {}
    for row in result:
        if row.job_type not in stats:
            stats[row.job_type] = {}
        stats[row.job_type][row.status] = row.count
    
    return stats


@router.get("/admin/audit", response_model=List[dict])
async def global_audit_log(
    limit: int = 100,
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    Global audit log (SYSTEM_ADMIN only).
    """
    sql = text("""
        SELECT tenant_id, action, resource_type, resource_id, 
               changes_json, metadata_json, created_at
        FROM audit_log
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    
    result = db.execute(sql, {"limit": min(limit, 200)})
    
    logs = []
    for row in result:
        logs.append({
            "tenant_id": row.tenant_id,
            "action": row.action,
            "resource_type": row.resource_type,
            "resource_id": row.resource_id,
            "changes": json.loads(row.changes_json) if row.changes_json else None,
            "metadata": json.loads(row.metadata_json) if row.metadata_json else None,
            "created_at": str(row.created_at)
        })
    
    return logs
