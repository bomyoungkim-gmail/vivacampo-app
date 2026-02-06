from fastapi import APIRouter, Depends, HTTPException, status
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership, require_role, get_current_tenant_id
from app.domain.value_objects.tenant_id import TenantId
from app.application.dtos.jobs import (
    CancelJobCommand,
    GetJobCommand,
    ListJobRunsCommand,
    ListJobsCommand,
    RetryJobCommand,
)
from app.infrastructure.di_container import ApiContainer
from app.schemas import JobView, JobRunView
from app.domain.audit import get_audit_logger
import structlog

logger = structlog.get_logger()
router = APIRouter(responses=DEFAULT_ERROR_RESPONSES, dependencies=[Depends(get_current_tenant_id)])


@router.get("/jobs", response_model=List[JobView])
async def list_jobs(
    aoi_id: Optional[UUID] = None,
    job_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """List jobs for the current tenant"""
    container = ApiContainer()
    use_case = container.list_jobs_use_case(db)
    jobs = await use_case.execute(
        ListJobsCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            aoi_id=aoi_id,
            job_type=job_type,
            status=status,
            limit=limit,
        )
    )

    return [
        JobView(
            id=job.id,
            aoi_id=job.aoi_id,
            job_type=job.job_type,
            status=job.status,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
        for job in jobs
    ]


@router.get("/jobs/{job_id}", response_model=JobView)
async def get_job(
    job_id: UUID,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """Get job details"""
    container = ApiContainer()
    use_case = container.get_job_use_case(db)
    job = await use_case.execute(GetJobCommand(tenant_id=TenantId(value=membership.tenant_id), job_id=job_id))

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobView(
        id=job.id,
        aoi_id=job.aoi_id,
        job_type=job.job_type,
        status=job.status,
        payload=job.payload,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/jobs/{job_id}/runs", response_model=List[JobRunView])
async def get_job_runs(
    job_id: UUID,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """Get job run history"""
    container = ApiContainer()
    use_case = container.list_job_runs_use_case(db)
    runs, job_exists = await use_case.execute(
        ListJobRunsCommand(tenant_id=TenantId(value=membership.tenant_id), job_id=job_id)
    )

    if not job_exists:
        raise HTTPException(status_code=404, detail="Job not found")

    return [
        JobRunView(
            id=run.id,
            job_id=run.job_id,
            attempt=run.attempt,
            status=run.status,
            metrics=run.metrics,
            error=run.error,
            started_at=run.started_at,
            finished_at=run.finished_at,
        )
        for run in runs
    ]


@router.post("/jobs/{job_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_job(
    job_id: UUID,
    membership: CurrentMembership = Depends(require_role("OPERATOR")),
    db: Session = Depends(get_db)
):
    """
    Retry a failed job.
    Requires OPERATOR or TENANT_ADMIN role.
    """
    container = ApiContainer()
    use_case = container.retry_job_use_case(db)
    try:
        ok = await use_case.execute(
            RetryJobCommand(tenant_id=TenantId(value=membership.tenant_id), job_id=job_id)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not ok:
        raise HTTPException(status_code=404, detail="Job not found")
    
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
async def cancel_job(
    job_id: UUID,
    membership: CurrentMembership = Depends(require_role("OPERATOR")),
    db: Session = Depends(get_db)
):
    """
    Cancel a pending or running job.
    Requires OPERATOR or TENANT_ADMIN role.
    """
    container = ApiContainer()
    use_case = container.cancel_job_use_case(db)
    try:
        ok = await use_case.execute(
            CancelJobCommand(tenant_id=TenantId(value=membership.tenant_id), job_id=job_id)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not ok:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log_job_action(
        tenant_id=str(membership.tenant_id),
        actor_id=str(membership.membership_id),
        job_id=str(job_id),
        action="CANCEL"
    )
    
    return {"message": "Job cancelled", "status": "CANCELLED"}