from fastapi import APIRouter, Depends, HTTPException, status
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership, require_role, get_current_tenant_id
from app.application.dtos.farms import CreateFarmCommand, ListFarmsCommand
from app.application.dtos.geocoding import GeocodeCommand
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.di_container import ApiContainer
from app.schemas import FarmCreate, FarmView
from app.domain.quotas import check_farm_quota, QuotaExceededError
from app.domain.audit import get_audit_logger
import structlog

logger = structlog.get_logger()
router = APIRouter(responses=DEFAULT_ERROR_RESPONSES, dependencies=[Depends(get_current_tenant_id)])


@router.post("/farms", response_model=FarmView, status_code=status.HTTP_201_CREATED)
async def create_farm(
    farm_data: FarmCreate,
    membership: CurrentMembership = Depends(require_role("OPERATOR")),
    db: Session = Depends(get_db)
):
    """
    Create a new farm.
    Requires OPERATOR or TENANT_ADMIN role.
    Enforces quota limits.
    """
    # Check quota
    try:
        check_farm_quota(str(membership.tenant_id), db)
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Farm quota exceeded: {e.current}/{e.limit}"
        )
    
    container = ApiContainer()
    use_case = container.create_farm_use_case(db)
    farm = await use_case.execute(
        CreateFarmCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            name=farm_data.name,
            timezone=farm_data.timezone,
        )
    )
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log(
        tenant_id=str(membership.tenant_id),
        actor_membership_id=str(membership.membership_id),
        action="CREATE",
        resource_type="farm",
        resource_id=str(farm.id),
        metadata={"name": farm_data.name, "timezone": farm_data.timezone}
    )
    return FarmView(
        id=farm.id,
        tenant_id=farm.tenant_id,
        name=farm.name,
        timezone=farm.timezone,
        aoi_count=farm.aoi_count,
        created_at=farm.created_at,
    )


@router.get("/farms", response_model=List[FarmView])
async def list_farms(
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    List all farms for the current tenant.
    """
    container = ApiContainer()
    use_case = container.list_farms_use_case(db)
    farms = await use_case.execute(ListFarmsCommand(tenant_id=TenantId(value=membership.tenant_id)))
    return [
        FarmView(
            id=farm.id,
            tenant_id=farm.tenant_id,
            name=farm.name,
            timezone=farm.timezone,
            aoi_count=farm.aoi_count,
            created_at=farm.created_at,
        )
        for farm in farms
    ]


@router.get("/farms/geocode")
async def geocode_location(
    q: str,
    membership: CurrentMembership = Depends(get_current_membership)
):
    """
    Proxy to Nominatim to avoid CORS/User-Agent issues in frontend.
    """
    if not q:
        return []

    container = ApiContainer()
    use_case = container.geocode_use_case()
    try:
        return await use_case.execute(GeocodeCommand(query=q))
    except Exception as e:
        logger.error("geocode_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Geocoding service unavailable")