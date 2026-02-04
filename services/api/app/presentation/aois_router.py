from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime, timedelta
from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership, require_role
from app.schemas import AOICreate, AOIView, AOIPatch, BackfillRequest
from app.domain.quotas import check_aoi_quota, check_backfill_quota, QuotaExceededError
from app.domain.audit import get_audit_logger
from app.infrastructure.s3_client import presign_row_s3_fields
import structlog
import hashlib

logger = structlog.get_logger()
router = APIRouter()


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
    
    # Validate geometry
    # Validate geometry
    geom_wkt = aoi_data.geometry  # Expect fully formed WKT from client
    
    sql = text("""
        INSERT INTO aois (tenant_id, farm_id, name, use_type, geom, area_ha, status)
        VALUES (
            :tenant_id, :farm_id, :name, :use_type, 
            ST_GeomFromText(:geom, 4326),
            ST_Area(ST_GeomFromText(:geom, 4326)::geography) / 10000,
            'ACTIVE'
        )
        RETURNING id, name, use_type, area_ha, status, created_at
    """)
    
    result = db.execute(sql, {
        "tenant_id": str(membership.tenant_id),
        "farm_id": str(aoi_data.farm_id),
        "name": aoi_data.name,
        "use_type": aoi_data.use_type,
        "geom": geom_wkt
    })
    db.commit()
    
    row = result.fetchone()
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log(
        tenant_id=str(membership.tenant_id),
        actor_membership_id=str(membership.membership_id),
        action="CREATE",
        resource_type="aoi",
        resource_id=str(row.id),
        metadata={"name": aoi_data.name, "use_type": aoi_data.use_type, "area_ha": row.area_ha}
    )

    # Trigger initial backfill for last 8 weeks on creation
    try:
        _create_backfill_job(str(membership.tenant_id), str(row.id), 56, db)
    except Exception as e:
        logger.error("auto_backfill_on_create_failed", aoi_id=str(row.id), exc_info=e)
    
    return AOIView(
        id=row.id,
        farm_id=aoi_data.farm_id,
        name=row.name,
        use_type=row.use_type,
        area_ha=row.area_ha,
        geometry=aoi_data.geometry,
        status=row.status,
        created_at=row.created_at
    )


@router.get("/aois", response_model=List[AOIView])
async def list_aois(
    farm_id: Optional[UUID] = None,
    status: Optional[str] = None,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """List all AOIs for the current tenant"""
    conditions = ["tenant_id = :tenant_id"]
    params = {"tenant_id": str(membership.tenant_id)}
    
    if farm_id:
        conditions.append("farm_id = :farm_id")
        params["farm_id"] = str(farm_id)
    
    if status:
        conditions.append("status = :status")
        params["status"] = status
    
    sql = text(f"""
        SELECT id, farm_id, name, use_type, area_ha, status, created_at,
               ST_AsText(geom) as geometry
        FROM aois
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC
        LIMIT 100
    """)
    
    result = db.execute(sql, params)
    
    aois = []
    for row in result:
        aois.append(AOIView(
            id=row.id,
            farm_id=row.farm_id,
            name=row.name,
            use_type=row.use_type,
            area_ha=row.area_ha,
            geometry=row.geometry,
            status=row.status,
            created_at=row.created_at
        ))
    
    return aois


    return [dict(row._mapping) for row in result]


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
    # Check existence and ownership
    sql_check = text("SELECT id FROM aois WHERE id = :aoi_id AND tenant_id = :tenant_id")
    result = db.execute(sql_check, {"aoi_id": str(aoi_id), "tenant_id": str(membership.tenant_id)}).fetchone()
    
    if not result:
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

    # Delete
    sql_delete = text("DELETE FROM aois WHERE id = :aoi_id")
    db.execute(sql_delete, {"aoi_id": str(aoi_id)})
    db.commit()


def _create_backfill_job(tenant_id: str, aoi_id: str, days: int, db: Session):
    """Helper to create and dispatch a backfill job for recent history"""
    from datetime import date, timedelta
    from app.config import settings
    import json
    
    to_date = date.today().isoformat()
    from_date = (date.today() - timedelta(days=days)).isoformat()
    
    job_key = hashlib.sha256(
        f"{tenant_id}{aoi_id}{from_date}{to_date}BACKFILL{settings.pipeline_version}".encode()
    ).hexdigest()
    
    sql = text("""
        INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
        VALUES (:tenant_id, :aoi_id, 'BACKFILL', :job_key, 'PENDING', :payload)
        ON CONFLICT (tenant_id, job_key) DO UPDATE
        SET status = 'PENDING', updated_at = now()
        RETURNING id
    """)
    
    payload = {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "from_date": from_date,
        "to_date": to_date,
        "cadence": "weekly"
    }
    
    result = db.execute(sql, {
        "tenant_id": tenant_id,
        "aoi_id": aoi_id,
        "job_key": job_key,
        "payload": json.dumps(payload)
    })
    db.commit()
    
    job_id = result.fetchone()[0]
    
    # Send to SQS
    from app.infrastructure.sqs_client import get_sqs_client
    sqs = get_sqs_client()
    
    # Ensure correct format for worker
    message_body = {
        "job_id": str(job_id),
        "job_type": "BACKFILL",
        "payload": payload
    }
    
    sqs.send_message(settings.sqs_queue_name, json.dumps(message_body))


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
    # Get current AOI
    sql = text("""
        SELECT name, use_type, status
        FROM aois
        WHERE id = :aoi_id AND tenant_id = :tenant_id
    """)
    
    result = db.execute(sql, {
        "aoi_id": str(aoi_id),
        "tenant_id": str(membership.tenant_id)
    }).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="AOI not found")
    
    # Build update
    updates = []
    params = {"aoi_id": str(aoi_id), "tenant_id": str(membership.tenant_id)}
    changes = {}
    
    if aoi_patch.name is not None:
        updates.append("name = :name")
        params["name"] = aoi_patch.name
        changes["name"] = {"before": result.name, "after": aoi_patch.name}
    
    if aoi_patch.use_type is not None:
        updates.append("use_type = :use_type")
        params["use_type"] = aoi_patch.use_type
        changes["use_type"] = {"before": result.use_type, "after": aoi_patch.use_type}
    
    if aoi_patch.status is not None:
        updates.append("status = :status")
        params["status"] = aoi_patch.status
        changes["status"] = {"before": result.status, "after": aoi_patch.status}
        
    trigger_reprocess = False
    if aoi_patch.geometry is not None:
        # Update geometry and recalculate area
        # We assume input is WKT or valid GeoJSON string
        updates.append("geom = ST_GeomFromText(:geom, 4326)")
        updates.append("area_ha = ST_Area(ST_GeomFromText(:geom, 4326)::geography) / 10000")
        params["geom"] = aoi_patch.geometry
        changes["geometry"] = "MODIFIED"
        trigger_reprocess = True
    
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    sql = text(f"""
        UPDATE aois
        SET {', '.join(updates)}
        WHERE id = :aoi_id AND tenant_id = :tenant_id
        RETURNING id, farm_id, name, use_type, area_ha, status, created_at, ST_AsText(geom) as geometry
    """)
    
    result = db.execute(sql, params)
    db.commit()
    
    row = result.fetchone()
    
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
    
    if trigger_reprocess:
        # Trigger backfill for last 8 weeks to refresh stats
        logger.info("triggering_auto_backfill", aoi_id=str(aoi_id))
        try:
            _create_backfill_job(str(membership.tenant_id), str(aoi_id), 56, db) # 8 weeks
        except Exception as e:
            logger.error("auto_backfill_failed", exc_info=e)
            # Don't fail the request, just log
    
    return AOIView(
        id=row.id,
        farm_id=row.farm_id,
        name=row.name,
        use_type=row.use_type,
        area_ha=row.area_ha,
        status=row.status,
        geometry=row.geometry,
        created_at=row.created_at
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
    # Verify AOI exists
    sql = text("SELECT id FROM aois WHERE id = :aoi_id AND tenant_id = :tenant_id")
    result = db.execute(sql, {
        "aoi_id": str(aoi_id),
        "tenant_id": str(membership.tenant_id)
    }).fetchone()
    
    if not result:
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
    
    # Create job
    from app.config import settings
    job_key = hashlib.sha256(
        f"{membership.tenant_id}{aoi_id}{backfill_data.from_date}{backfill_data.to_date}BACKFILL{settings.pipeline_version}".encode()
    ).hexdigest()
    
    sql = text("""
        INSERT INTO jobs (tenant_id, aoi_id, job_type, job_key, status, payload_json)
        VALUES (:tenant_id, :aoi_id, 'BACKFILL', :job_key, 'PENDING', :payload)
        ON CONFLICT (tenant_id, job_key) DO UPDATE
        SET status = 'PENDING', updated_at = now()
        RETURNING id
    """)
    
    import json
    result = db.execute(sql, {
        "tenant_id": str(membership.tenant_id),
        "aoi_id": str(aoi_id),
        "job_key": job_key,
        "payload": json.dumps({
            "tenant_id": str(membership.tenant_id),
            "aoi_id": str(aoi_id),
            "from_date": backfill_data.from_date,
            "to_date": backfill_data.to_date,
            "cadence": backfill_data.cadence
        })
    })
    db.commit()
    
    job_id = result.fetchone()[0]
    
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
    
    # Send to SQS
    from app.infrastructure.sqs_client import get_sqs_client
    sqs = get_sqs_client()
    
    message_body = {
        "job_id": str(job_id),
        "job_type": "BACKFILL",
        "payload": {
            "tenant_id": str(membership.tenant_id),
            "aoi_id": str(aoi_id),
            "from_date": backfill_data.from_date,
            "to_date": backfill_data.to_date,
            "cadence": backfill_data.cadence
        }
    }
    
    sqs.send_message(settings.sqs_queue_name, json.dumps(message_body))
    
    return {
        "job_id": job_id,
        "status": "PENDING",
        "weeks_count": weeks_count,
        "message": "Backfill job created successfully"
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
    sql = text("""
        SELECT ndvi_s3_uri, anomaly_s3_uri, quicklook_s3_uri, 
               ndwi_s3_uri, ndmi_s3_uri, savi_s3_uri, false_color_s3_uri, true_color_s3_uri,
               
               ndre_s3_uri, reci_s3_uri, gndvi_s3_uri, evi_s3_uri,
               msi_s3_uri, nbr_s3_uri, bsi_s3_uri, ari_s3_uri, cri_s3_uri,

               ndvi_mean, ndvi_min, ndvi_max, ndvi_std,
               ndwi_mean, ndwi_min, ndwi_max, ndwi_std,
               ndmi_mean, ndmi_min, ndmi_max, ndmi_std,
               savi_mean, savi_min, savi_max, savi_std,
               anomaly_mean, anomaly_std,
               
               ndre_mean, ndre_std, reci_mean, reci_std,
               gndvi_mean, gndvi_std, evi_mean, evi_std,
               msi_mean, msi_std, nbr_mean, nbr_std,
               bsi_mean, bsi_std, ari_mean, ari_std,
               cri_mean, cri_std,

               year, week
        FROM derived_assets
        WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
        ORDER BY year DESC, week DESC
        LIMIT 1
    """)
    
    result = db.execute(sql, {
        "tenant_id": str(membership.tenant_id),
        "aoi_id": str(aoi_id)
    }).fetchone()
    
    if not result:
        return {}

    assets = dict(result._mapping)
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
    sql = text("""
        SELECT 
            year, week,
            ndvi_mean, ndvi_min, ndvi_max, ndvi_std,
            ndwi_mean, ndwi_min, ndwi_max, ndwi_std,
            ndmi_mean, ndmi_min, ndmi_max, ndmi_std,
            savi_mean, savi_min, savi_max, savi_std,
            anomaly_mean,
            
            ndre_mean, reci_mean, gndvi_mean, evi_mean,
            msi_mean, nbr_mean, bsi_mean, ari_mean, cri_mean
        FROM derived_assets
        WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
        ORDER BY year DESC, week DESC
        LIMIT :limit
    """)
    
    result = db.execute(sql, {
        "tenant_id": str(membership.tenant_id),
        "aoi_id": str(aoi_id),
        "limit": limit
    })
    
    return [dict(row._mapping) for row in result]
