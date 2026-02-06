from fastapi import APIRouter, Depends, HTTPException, status
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.auth.dependencies import get_current_system_admin
from app.schemas import TenantView, TenantCreate, TenantPatch, SystemJobView
from app.domain.audit import get_audit_logger
from app.application.dtos.system_admin import (
    CreateTenantCommand,
    GlobalAuditLogCommand,
    ListMissingWeeksCommand,
    ListSystemJobsCommand,
    ListTenantsCommand,
    ReprocessMissingAoisCommand,
    ReprocessMissingWeeksCommand,
    RetryJobCommand,
    UpdateTenantCommand,
)
from app.infrastructure.di_container import ApiContainer
import structlog
import json

logger = structlog.get_logger()
router = APIRouter(responses=DEFAULT_ERROR_RESPONSES)


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
    container = ApiContainer()
    use_case = container.list_tenants_use_case(db)
    rows = await use_case.execute(ListTenantsCommand(tenant_type=tenant_type, limit=limit))
    return [
        TenantView(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            status=row["status"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


@router.post("/admin/tenants", response_model=TenantView, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new tenant (SYSTEM_ADMIN only).
    """
    container = ApiContainer()
    use_case = container.create_tenant_use_case(db)
    row = await use_case.execute(
        CreateTenantCommand(name=tenant_data.name, tenant_type=tenant_data.type)
    )
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log(
        tenant_id="SYSTEM",
        actor_membership_id=None,
        action="CREATE_TENANT",
        resource_type="tenant",
        resource_id=str(row["id"]),
        metadata={"name": tenant_data.name, "type": tenant_data.type}
    )
    
    return TenantView(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        status=row["status"],
        created_at=row["created_at"],
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
    container = ApiContainer()
    use_case = container.update_tenant_use_case(db)
    result = await use_case.execute(
        UpdateTenantCommand(tenant_id=tenant_id, status=tenant_patch.status)
    )

    if not result:
        raise HTTPException(status_code=404, detail="Tenant not found")

    old_status = result["before"]
    
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
    container = ApiContainer()
    use_case = container.list_system_jobs_use_case(db)
    rows = await use_case.execute(
        ListSystemJobsCommand(status=status, job_type=job_type, limit=limit)
    )
    return [
        SystemJobView(
            id=row["id"],
            tenant_id=row["tenant_id"],
            aoi_id=row["aoi_id"],
            aoi_name=row.get("aoi_name"),
            farm_name=row.get("farm_name"),
            job_type=row["job_type"],
            job_key=row["job_key"],
            status=row["status"],
            error_message=row.get("error_message"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


@router.post("/admin/jobs/{job_id}/retry")
async def admin_retry_job(
    job_id: UUID,
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    Retry any job (SYSTEM_ADMIN only).
    """
    container = ApiContainer()
    use_case = container.system_retry_job_use_case(db)
    ok = await use_case.execute(RetryJobCommand(job_id=job_id))
    if not ok:
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
    container = ApiContainer()
    use_case = container.reprocess_missing_aois_use_case(db)
    result = await use_case.execute(
        ReprocessMissingAoisCommand(days=days, limit=limit)
    )

    audit = get_audit_logger(db)
    audit.log(
        tenant_id="SYSTEM",
        actor_membership_id=None,
        action="ADMIN_REPROCESS_MISSING_AOIS",
        resource_type="aoi",
        resource_id=None,
        metadata={
            "queued": result.get("queued"),
            "from_date": result.get("from_date"),
            "to_date": result.get("to_date"),
        }
    )

    return result


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
    container = ApiContainer()
    use_case = container.list_missing_weeks_use_case(db)
    return await use_case.execute(ListMissingWeeksCommand(weeks=weeks, limit=limit))


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
    container = ApiContainer()
    use_case = container.reprocess_missing_weeks_use_case(db)
    result = await use_case.execute(
        ReprocessMissingWeeksCommand(
            weeks=weeks,
            limit=limit,
            max_runs_per_aoi=max_runs_per_aoi,
        )
    )

    audit = get_audit_logger(db)
    audit.log(
        tenant_id="SYSTEM",
        actor_membership_id=None,
        action="ADMIN_REPROCESS_MISSING_WEEKS",
        resource_type="aoi",
        resource_id=None,
        metadata={
            "weeks": result.get("weeks"),
            "limit": result.get("limit"),
            "queued": result.get("queued"),
        }
    )

    return result


@router.get("/admin/ops/health")
async def system_health(
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    System-wide health check (SYSTEM_ADMIN only).
    """
    container = ApiContainer()
    use_case = container.system_health_use_case(db)
    return await use_case.execute()


@router.get("/admin/ops/queues")
async def queue_stats(
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    Queue statistics (SYSTEM_ADMIN only).
    """
    container = ApiContainer()
    use_case = container.queue_stats_use_case(db)
    return await use_case.execute()


@router.get("/admin/audit", response_model=List[dict])
async def global_audit_log(
    limit: int = 100,
    system_admin = Depends(get_current_system_admin),
    db: Session = Depends(get_db)
):
    """
    Global audit log (SYSTEM_ADMIN only).
    """
    container = ApiContainer()
    use_case = container.global_audit_log_use_case(db)
    rows = await use_case.execute(GlobalAuditLogCommand(limit=limit))
    logs = []
    for row in rows:
        logs.append(
            {
                "tenant_id": row["tenant_id"],
                "action": row["action"],
                "resource_type": row["resource_type"],
                "resource_id": row["resource_id"],
                "changes": json.loads(row["changes_json"]) if row["changes_json"] else None,
                "metadata": json.loads(row["metadata_json"]) if row["metadata_json"] else None,
                "created_at": str(row["created_at"]),
            }
        )
    return logs