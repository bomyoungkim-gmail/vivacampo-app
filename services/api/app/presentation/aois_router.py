from fastapi import APIRouter, Depends, HTTPException, status, Header
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone
from app.auth.dependencies import get_current_membership, CurrentMembership, require_role, get_current_tenant_id
from app.schemas import (
    AOICreate,
    AOIView,
    AOIPatch,
    BackfillRequest,
    AoiSplitSimulationRequest,
    AoiSplitSimulationResponse,
    AoiSplitCreateRequest,
    AoiSplitCreateResponse,
    AoiStatusRequest,
    AoiStatusResponse,
)
from app.domain.quotas import QuotaExceededError
from app.domain.value_objects.tenant_id import TenantId
from app.application.dtos.aois import (
    CreateAoiCommand,
    ListAoisCommand,
    SimulateSplitCommand,
    SplitAoiCommand,
    SplitPolygonInput,
    AoiStatusCommand,
)
from app.application.dtos.aoi_management import (
    AoiAssetsCommand,
    AoiHistoryCommand,
    DeleteAoiCommand,
    RequestBackfillCommand,
    UpdateAoiCommand,
)
from app.infrastructure.di_container import ApiContainer, get_container
from app.infrastructure.s3_client import presign_row_s3_fields
import structlog

logger = structlog.get_logger()
router = APIRouter(responses=DEFAULT_ERROR_RESPONSES, dependencies=[Depends(get_current_tenant_id)])


@router.post("/aois", response_model=AOIView, status_code=status.HTTP_201_CREATED)
async def create_aoi(
    aoi_data: AOICreate,
    membership: CurrentMembership = Depends(require_role("EDITOR")),
    container: ApiContainer = Depends(get_container)
):
    """
    Create a new Area of Interest (AOI).
    Requires EDITOR or TENANT_ADMIN role.
    Enforces quota limits.
    """
    quota_service = container.quota_service()

    # Check quota
    try:
        quota_service.check_aoi_quota(str(membership.tenant_id))
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"AOI quota exceeded: {e.current}/{e.limit}"
        )
    
    geom_wkt = aoi_data.geometry  # Expect fully formed WKT from client

    use_case = container.create_aoi_use_case()
    try:
        aoi = await use_case.execute(
            CreateAoiCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                farm_id=aoi_data.farm_id,
                name=aoi_data.name,
                use_type=aoi_data.use_type,
                geometry_wkt=geom_wkt,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    
    # Audit log
    audit = container.audit_logger()
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
        backfill_use_case = container.request_backfill_use_case()
        await backfill_use_case.execute(
            RequestBackfillCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                aoi_id=aoi.id,
                from_date=(datetime.now(timezone.utc) - timedelta(days=56)).date().isoformat(),
                to_date=datetime.now(timezone.utc).date().isoformat(),
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


@router.post("/aois/simulate-split", response_model=AoiSplitSimulationResponse)
async def simulate_split(
    payload: AoiSplitSimulationRequest,
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    container: ApiContainer = Depends(get_container),
):
    """
    Simulate split of a macro polygon into paddocks (voronoi or grid).
    """
    use_case = container.simulate_split_use_case()
    try:
        result = await use_case.execute(
            SimulateSplitCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                geometry_wkt=payload.geometry_wkt,
                mode=payload.mode,
                target_count=payload.target_count,
                max_area_ha=payload.max_area_ha,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return AoiSplitSimulationResponse(
        polygons=[
            {"geometry_wkt": poly.geometry_wkt, "area_ha": poly.area_ha}
            for poly in result.polygons
        ],
        warnings=result.warnings,
    )


@router.post("/aois/split", response_model=AoiSplitCreateResponse)
async def split_aois(
    payload: AoiSplitCreateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    container: ApiContainer = Depends(get_container),
):
    """
    Persist split polygons as AOIs and optionally enqueue backfill jobs.
    """
    use_case = container.split_aoi_use_case()
    if not idempotency_key:
        import hashlib

        serialized = "|".join(
            [str(payload.parent_aoi_id)]
            + [f"{poly.geometry_wkt}:{poly.name or ''}" for poly in payload.polygons]
        )
        idempotency_key = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    try:
        result = await use_case.execute(
            SplitAoiCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                parent_aoi_id=payload.parent_aoi_id,
                polygons=[
                    SplitPolygonInput(
                        geometry_wkt=poly.geometry_wkt,
                        name=poly.name,
                    )
                    for poly in payload.polygons
                ],
                max_area_ha=payload.max_area_ha,
                idempotency_key=idempotency_key,
            )
        )
    except ValueError as exc:
        message = str(exc)
        if message == "PARENT_AOI_NOT_FOUND":
            raise HTTPException(status_code=404, detail="Parent AOI not found")
        if message == "POLYGONS_REQUIRED":
            raise HTTPException(status_code=422, detail="Polygons are required")
        if message.startswith("TALHAO_") and message.endswith("_EXCEEDS_MAX_AREA"):
            raise HTTPException(status_code=422, detail="AOI exceeds max area")
        raise HTTPException(status_code=422, detail=message)

    job_ids = []
    if payload.enqueue_jobs and not result.idempotent:
        backfill_use_case = container.request_backfill_use_case()
        for aoi_id in result.created_ids:
            response = await backfill_use_case.execute(
                RequestBackfillCommand(
                    tenant_id=TenantId(value=membership.tenant_id),
                    aoi_id=aoi_id,
                    from_date=(datetime.now(timezone.utc) - timedelta(days=56)).date().isoformat(),
                    to_date=datetime.now(timezone.utc).date().isoformat(),
                    cadence="weekly",
                )
            )
            job_ids.append(response.job_id)

    return AoiSplitCreateResponse(created=len(result.created_ids), job_ids=job_ids, warnings=[])


@router.post("/aois/status", response_model=AoiStatusResponse)
async def get_aois_status(
    payload: AoiStatusRequest,
    membership: CurrentMembership = Depends(get_current_membership),
    container: ApiContainer = Depends(get_container),
):
    """
    Return processing status for a list of AOIs.
    """
    use_case = container.aoi_status_use_case()
    result = await use_case.execute(
        AoiStatusCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            aoi_ids=payload.aoi_ids,
        )
    )
    return AoiStatusResponse(items=[item.model_dump() for item in result.items])


@router.get("/aois", response_model=List[AOIView])
async def list_aois(
    farm_id: Optional[UUID] = None,
    status: Optional[str] = None,
    membership: CurrentMembership = Depends(get_current_membership),
    container: ApiContainer = Depends(get_container)
):
    """List all AOIs for the current tenant"""
    use_case = container.list_aois_use_case()
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
    membership: CurrentMembership = Depends(require_role("EDITOR")),
    container: ApiContainer = Depends(get_container)
):
    """
    Delete an AOI.
    Cascades to derived_assets and observations via DB constraints.
    """
    use_case = container.delete_aoi_use_case()
    deleted = await use_case.execute(DeleteAoiCommand(tenant_id=TenantId(value=membership.tenant_id), aoi_id=aoi_id))

    if not deleted:
        raise HTTPException(status_code=404, detail="AOI not found")

    # Audit log
    audit = container.audit_logger()
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
    membership: CurrentMembership = Depends(require_role("EDITOR")),
    container: ApiContainer = Depends(get_container)
):
    """
    Update AOI (name, use_type, status, geometry).
    If geometry is updated, a backfill for the last 8 weeks is triggered.
    """
    use_case = container.update_aoi_use_case()

    if (
        aoi_patch.name is None
        and aoi_patch.use_type is None
        and aoi_patch.status is None
        and aoi_patch.geometry is None
    ):
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
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
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

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
    audit = container.audit_logger()
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
            backfill_use_case = container.request_backfill_use_case()
            await backfill_use_case.execute(
                RequestBackfillCommand(
                    tenant_id=TenantId(value=membership.tenant_id),
                    aoi_id=aoi_id,
                    from_date=(datetime.now(timezone.utc) - timedelta(days=56)).date().isoformat(),
                    to_date=datetime.now(timezone.utc).date().isoformat(),
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
    membership: CurrentMembership = Depends(require_role("EDITOR")),
    container: ApiContainer = Depends(get_container)
):
    """
    Request backfill processing for an AOI.
    Creates BACKFILL job that will orchestrate PROCESS_WEEK jobs.
    Enforces quota limits.
    """
    quota_service = container.quota_service()
    aoi_repo = container.aoi_repository()
    aoi = await aoi_repo.get_by_id(TenantId(value=membership.tenant_id), aoi_id)
    if not aoi:
        raise HTTPException(status_code=404, detail="AOI not found")
    
    # Calculate weeks
    from_dt = datetime.strptime(backfill_data.from_date, "%Y-%m-%d")
    to_dt = datetime.strptime(backfill_data.to_date, "%Y-%m-%d")
    weeks_count = int((to_dt - from_dt).days / 7) + 1
    
    # Check quota
    try:
        quota_service.check_backfill_quota(str(membership.tenant_id), weeks_count)
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Backfill quota exceeded: {str(e)}"
        )
    
    backfill_use_case = container.request_backfill_use_case()
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
    audit = container.audit_logger()
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
    container: ApiContainer = Depends(get_container)
):
    """
    Get latest derived assets (NDVI, etc) for an AOI.
    """
    use_case = container.aoi_assets_use_case()
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
    container: ApiContainer = Depends(get_container)
):
    """
    Get historical statistics for charts.
    """
    use_case = container.aoi_history_use_case()
    return await use_case.execute(
        AoiHistoryCommand(tenant_id=TenantId(value=membership.tenant_id), aoi_id=aoi_id, limit=limit)
    )
