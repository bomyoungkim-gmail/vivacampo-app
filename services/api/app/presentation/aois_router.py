from fastapi import APIRouter, Depends, HTTPException, status
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership, require_role, get_current_tenant_id
from app.schemas import AOICreate, AOIView, AOIPatch, BackfillRequest
from app.domain.quotas import check_aoi_quota, check_backfill_quota, QuotaExceededError
from app.domain.audit import get_audit_logger
from app.domain.value_objects.tenant_id import TenantId
from app.application.dtos.aois import CreateAoiCommand, ListAoisCommand
from app.application.dtos.aoi_management import (
    AoiAssetsCommand,
    AoiHistoryCommand,
    DeleteAoiCommand,
    RequestBackfillCommand,
    UpdateAoiCommand,
)
from app.infrastructure.di_container import ApiContainer
from app.infrastructure.s3_client import presign_row_s3_fields
import structlog

logger = structlog.get_logger()
router = APIRouter(responses=DEFAULT_ERROR_RESPONSES, dependencies=[Depends(get_current_tenant_id)])


@router.post("/aois", response_model=AOIView, status_code=status.HTTP_201_CREATED)
async def create_aoi(
    aoi_data: AOICreate,
    membership: CurrentMembership = Depends(require_role("OPERATOR")),
    db: Session = Depends(get_db)
):
    """
    Create a new Area of Interest (AOI).
    Requires OPERATOR or TENANT_ADMIN role.
    Enforces quota limits.
    """
    # Check quota
    try:
        check_aoi_quota(str(membership.tenant_id), db)
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"AOI quota exceeded: {e.current}/{e.limit}"
        )
    
    geom_wkt = aoi_data.geometry  # Expect fully formed WKT from client

    container = ApiContainer()
    use_case = container.create_aoi_use_case(db)
    aoi = await use_case.execute(
        CreateAoiCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            farm_id=aoi_data.farm_id,
            name=aoi_data.name,
            use_type=aoi_data.use_type,
            geometry_wkt=geom_wkt,
        )
    )
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log(
        tenant_id=str(membership.tenant_id),
        actor_membership_id=str(membership.membership_id),
        action="CREATE",
        resource_type="aoi",
        resource_id=str(aoi.id),
        metadata={"name": aoi_data.name, "use_type": aoi_data.use_type, "area_ha": aoi.area_ha}
    )

    # Trigger initial backfill for last 8 weeks on creation
    try:
        backfill_use_case = container.request_backfill_use_case(db)
        await backfill_use_case.execute(
            RequestBackfillCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                aoi_id=aoi.id,
                from_date=(datetime.utcnow() - timedelta(days=56)).date().isoformat(),
                to_date=datetime.utcnow().date().isoformat(),
                cadence="weekly",
            )
        )
    except Exception as e:
        logger.error("auto_backfill_on_create_failed", aoi_id=str(aoi.id), exc_info=e)

    return AOIView(
        id=aoi.id,
        farm_id=aoi.farm_id,
        name=aoi.name,
        use_type=aoi.use_type,
        area_ha=aoi.area_ha,
        geometry=aoi.geometry,
        status=aoi.status,
        created_at=aoi.created_at,
    )


@router.get("/aois", response_model=List[AOIView])
async def list_aois(
    farm_id: Optional[UUID] = None,
    status: Optional[str] = None,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """List all AOIs for the current tenant"""
    container = ApiContainer()
    use_case = container.list_aois_use_case(db)
    aois = await use_case.execute(
        ListAoisCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            farm_id=farm_id,
            status=status,
        )
    )

    return [
        AOIView(
            id=aoi.id,
            farm_id=aoi.farm_id,
            name=aoi.name,
            use_type=aoi.use_type,
            area_ha=aoi.area_ha,
            geometry=aoi.geometry,
            status=aoi.status,
            created_at=aoi.created_at,
        )
        for aoi in aois
    ]


@router.delete("/aois/{aoi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_aoi(
    aoi_id: UUID,
    membership: CurrentMembership = Depends(require_role("OPERATOR")),
    db: Session = Depends(get_db)
):
    """
    Delete an AOI.
    Cascades to derived_assets and observations via DB constraints.
    """
    container = ApiContainer()
    use_case = container.delete_aoi_use_case(db)
    deleted = await use_case.execute(DeleteAoiCommand(tenant_id=TenantId(value=membership.tenant_id), aoi_id=aoi_id))

    if not deleted:
        raise HTTPException(status_code=404, detail="AOI not found")

    # Audit log
    audit = get_audit_logger(db)
    audit.log(
        tenant_id=str(membership.tenant_id),
        actor_membership_id=str(membership.membership_id),
        action="DELETE",
        resource_type="aoi",
        resource_id=str(aoi_id),
        metadata={}
    )



@router.patch("/aois/{aoi_id}", response_model=AOIView)
async def update_aoi(
    aoi_id: UUID,
    aoi_patch: AOIPatch,
    membership: CurrentMembership = Depends(require_role("OPERATOR")),
    db: Session = Depends(get_db)
):
    """
    Update AOI (name, use_type, status, geometry).
    If geometry is updated, a backfill for the last 8 weeks is triggered.
    """
    container = ApiContainer()
    use_case = container.update_aoi_use_case(db)

    if (
        aoi_patch.name is None
        and aoi_patch.use_type is None
        and aoi_patch.status is None
        and aoi_patch.geometry is None
    ):
        raise HTTPException(status_code=400, detail="No fields to update")

    result = await use_case.execute(
        UpdateAoiCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            aoi_id=aoi_id,
            name=aoi_patch.name,
            use_type=aoi_patch.use_type,
            status=aoi_patch.status,
            geometry_wkt=aoi_patch.geometry,
        )
    )

    if not result:
        raise HTTPException(status_code=404, detail="AOI not found")

    changes = {}
    if aoi_patch.name is not None:
        changes["name"] = {"after": aoi_patch.name}
    if aoi_patch.use_type is not None:
        changes["use_type"] = {"after": aoi_patch.use_type}
    if aoi_patch.status is not None:
        changes["status"] = {"after": aoi_patch.status}
    if aoi_patch.geometry is not None:
        changes["geometry"] = "MODIFIED"
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log(
        tenant_id=str(membership.tenant_id),
        actor_membership_id=str(membership.membership_id),
        action="UPDATE",
        resource_type="aoi",
        resource_id=str(aoi_id),
        changes=changes
    )

    if result.geometry_changed:
        logger.info("triggering_auto_backfill", aoi_id=str(aoi_id))
        try:
            backfill_use_case = container.request_backfill_use_case(db)
            await backfill_use_case.execute(
                RequestBackfillCommand(
                    tenant_id=TenantId(value=membership.tenant_id),
                    aoi_id=aoi_id,
                    from_date=(datetime.utcnow() - timedelta(days=56)).date().isoformat(),
                    to_date=datetime.utcnow().date().isoformat(),
                    cadence="weekly",
                )
            )
        except Exception as e:
            logger.error("auto_backfill_failed", exc_info=e)

    return AOIView(
        id=result.id,
        farm_id=result.farm_id,
        name=result.name,
        use_type=result.use_type,
        area_ha=result.area_ha,
        status=result.status,
        geometry=result.geometry,
        created_at=result.created_at,
    )


@router.post("/aois/{aoi_id}/backfill", status_code=status.HTTP_202_ACCEPTED)
async def request_backfill(
    aoi_id: UUID,
    backfill_data: BackfillRequest,
    membership: CurrentMembership = Depends(require_role("OPERATOR")),
    db: Session = Depends(get_db)
):
    """
    Request backfill processing for an AOI.
    Creates BACKFILL job that will orchestrate PROCESS_WEEK jobs.
    Enforces quota limits.
    """
    container = ApiContainer()
    aoi_repo = container.aoi_repository(db)
    aoi = await aoi_repo.get_by_id(TenantId(value=membership.tenant_id), aoi_id)
    if not aoi:
        raise HTTPException(status_code=404, detail="AOI not found")
    
    # Calculate weeks
    from_dt = datetime.strptime(backfill_data.from_date, "%Y-%m-%d")
    to_dt = datetime.strptime(backfill_data.to_date, "%Y-%m-%d")
    weeks_count = int((to_dt - from_dt).days / 7) + 1
    
    # Check quota
    try:
        check_backfill_quota(str(membership.tenant_id), weeks_count, db)
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Backfill quota exceeded: {str(e)}"
        )
    
    backfill_use_case = container.request_backfill_use_case(db)
    result = await backfill_use_case.execute(
        RequestBackfillCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            aoi_id=aoi_id,
            from_date=backfill_data.from_date,
            to_date=backfill_data.to_date,
            cadence=backfill_data.cadence,
        )
    )
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log_backfill_request(
        tenant_id=str(membership.tenant_id),
        actor_id=str(membership.membership_id),
        aoi_id=str(aoi_id),
        from_date=backfill_data.from_date,
        to_date=backfill_data.to_date,
        weeks_count=weeks_count
    )
    
    return {
        "job_id": result.job_id,
        "status": result.status,
        "weeks_count": result.weeks_count,
        "message": result.message
    }


@router.get("/aois/{aoi_id}/assets", response_model=dict)
async def get_aoi_assets(
    aoi_id: UUID,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    Get latest derived assets (NDVI, etc) for an AOI.
    """
    container = ApiContainer()
    use_case = container.aoi_assets_use_case(db)
    assets = await use_case.execute(
        AoiAssetsCommand(tenant_id=TenantId(value=membership.tenant_id), aoi_id=aoi_id)
    )

    if not assets:
        return {}
    s3_fields = [
        "ndvi_s3_uri",
        "anomaly_s3_uri",
        "quicklook_s3_uri",
        "ndwi_s3_uri",
        "ndmi_s3_uri",
        "savi_s3_uri",
        "false_color_s3_uri",
        "true_color_s3_uri",
        "ndre_s3_uri",
        "reci_s3_uri",
        "gndvi_s3_uri",
        "evi_s3_uri",
        "msi_s3_uri",
        "nbr_s3_uri",
        "bsi_s3_uri",
        "ari_s3_uri",
        "cri_s3_uri",
    ]
    return presign_row_s3_fields(assets, s3_fields)


@router.get("/aois/{aoi_id}/history", response_model=List[dict])
async def get_aoi_history(
    aoi_id: UUID,
    limit: int = 52,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    Get historical statistics for charts.
    """
    container = ApiContainer()
    use_case = container.aoi_history_use_case(db)
    return await use_case.execute(
        AoiHistoryCommand(tenant_id=TenantId(value=membership.tenant_id), aoi_id=aoi_id, limit=limit)
    )