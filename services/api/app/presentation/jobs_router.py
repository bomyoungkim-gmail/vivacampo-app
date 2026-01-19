from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership, require_role
from app.schemas import JobView, JobRunView
from app.domain.audit import get_audit_logger
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.get("/jobs", response_model=List[JobView])
def list_jobs(
    aoi_id: Optional[UUID] = None,
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """List jobs for the current tenant"""
    conditions = ["tenant_id = :tenant_id"]
    params = {
        "tenant_id": str(membership.tenant_id),
        "limit": min(limit, 100)
    }
    
    if aoi_id:
        conditions.append("aoi_id = :aoi_id")
        params["aoi_id"] = str(aoi_id)
    
    if job_type:
        conditions.append("job_type = :job_type")
        params["job_type"] = job_type
    
    if status:
        conditions.append("status = :status")
        params["status"] = status
    
    sql = text(f"""
        SELECT id, aoi_id, job_type, status, created_at, updated_at
        FROM jobs
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    
    result = db.execute(sql, params)
    
    jobs = []
    for row in result:
        jobs.append(JobView(
            id=row.id,
            aoi_id=row.aoi_id,
            job_type=row.job_type,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at
        ))
    
    return jobs


@router.get("/jobs/{job_id}", response_model=JobView)
def get_job(
    job_id: UUID,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """Get job details"""
    sql = text("""
        SELECT id, aoi_id, job_type, status, payload_json, created_at, updated_at
        FROM jobs
        WHERE id = :job_id AND tenant_id = :tenant_id
    """)
    
    result = db.execute(sql, {
        "job_id": str(job_id),
        "tenant_id": str(membership.tenant_id)
    }).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    
    import json
    return JobView(
        id=result.id,
        aoi_id=result.aoi_id,
        job_type=result.job_type,
        status=result.status,
        payload=json.loads(result.payload_json) if result.payload_json else None,
        created_at=result.created_at,
        updated_at=result.updated_at
    )


@router.get("/jobs/{job_id}/runs", response_model=List[JobRunView])
def get_job_runs(
    job_id: UUID,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """Get job run history"""
    # Verify job belongs to tenant
    sql = text("SELECT id FROM jobs WHERE id = :job_id AND tenant_id = :tenant_id")
    result = db.execute(sql, {
        "job_id": str(job_id),
        "tenant_id": str(membership.tenant_id)
    }).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get runs
    sql = text("""
        SELECT id, attempt, status, metrics_json, error_json, started_at, finished_at
        FROM job_runs
        WHERE job_id = :job_id
        ORDER BY attempt DESC
        LIMIT 10
    """)
    
    result = db.execute(sql, {"job_id": str(job_id)})
    
    runs = []
    import json
    for row in result:
        runs.append(JobRunView(
            id=row.id,
            job_id=job_id,
            attempt=row.attempt,
            status=row.status,
            metrics=json.loads(row.metrics_json) if row.metrics_json else None,
            error=json.loads(row.error_json) if row.error_json else None,
            started_at=row.started_at,
            finished_at=row.finished_at
        ))
    
    return runs


@router.post("/jobs/{job_id}/retry", status_code=status.HTTP_202_ACCEPTED)
def retry_job(
    job_id: UUID,
    membership: CurrentMembership = Depends(require_role("OPERATOR")),
    db: Session = Depends(get_db)
):
    """
    Retry a failed job.
    Requires OPERATOR or TENANT_ADMIN role.
    """
    # Verify job exists and is in FAILED state
    sql = text("""
        SELECT status FROM jobs
        WHERE id = :job_id AND tenant_id = :tenant_id
    """)
    
    result = db.execute(sql, {
        "job_id": str(job_id),
        "tenant_id": str(membership.tenant_id)
    }).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if result.status not in ["FAILED", "CANCELLED"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry job in {result.status} state"
        )
    
    # Update job status
    sql = text("""
        UPDATE jobs
        SET status = 'PENDING', updated_at = now()
        WHERE id = :job_id AND tenant_id = :tenant_id
    """)
    
    db.execute(sql, {
        "job_id": str(job_id),
        "tenant_id": str(membership.tenant_id)
    })
    db.commit()
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log_job_action(
        tenant_id=str(membership.tenant_id),
        actor_id=str(membership.membership_id),
        job_id=str(job_id),
        action="RETRY"
    )
    
    # TODO: Re-send to SQS
    
    return {"message": "Job retry requested", "status": "PENDING"}


@router.post("/jobs/{job_id}/cancel", status_code=status.HTTP_202_ACCEPTED)
def cancel_job(
    job_id: UUID,
    membership: CurrentMembership = Depends(require_role("OPERATOR")),
    db: Session = Depends(get_db)
):
    """
    Cancel a pending or running job.
    Requires OPERATOR or TENANT_ADMIN role.
    """
    # Verify job exists
    sql = text("""
        SELECT status FROM jobs
        WHERE id = :job_id AND tenant_id = :tenant_id
    """)
    
    result = db.execute(sql, {
        "job_id": str(job_id),
        "tenant_id": str(membership.tenant_id)
    }).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if result.status not in ["PENDING", "RUNNING"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job in {result.status} state"
        )
    
    # Update job status
    sql = text("""
        UPDATE jobs
        SET status = 'CANCELLED', updated_at = now()
        WHERE id = :job_id AND tenant_id = :tenant_id
    """)
    
    db.execute(sql, {
        "job_id": str(job_id),
        "tenant_id": str(membership.tenant_id)
    })
    db.commit()
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log_job_action(
        tenant_id=str(membership.tenant_id),
        actor_id=str(membership.membership_id),
        job_id=str(job_id),
        action="CANCEL"
    )
    
    return {"message": "Job cancelled", "status": "CANCELLED"}
