from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.auth.dependencies import get_current_system_admin
from app.schemas import TenantView, TenantCreate, TenantPatch, SystemJobView, DLQMessageView
from app.domain.audit import get_audit_logger
import structlog
import json

logger = structlog.get_logger()
router = APIRouter()


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
        conditions.append("status = :status")
        params["status"] = status
    
    if job_type:
        conditions.append("job_type = :job_type")
        params["job_type"] = job_type
    
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    sql = text(f"""
        SELECT id, tenant_id, aoi_id, job_type, status, created_at, updated_at
        FROM jobs
        {where_clause}
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    
    result = db.execute(sql, params)
    
    jobs = []
    for row in result:
        jobs.append(SystemJobView(
            id=row.id,
            tenant_id=row.tenant_id,
            aoi_id=row.aoi_id,
            job_type=row.job_type,
            status=row.status,
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
