from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership, require_role
from app.application.farms import CreateFarmUseCase, ListFarmsUseCase
from app.schemas import FarmCreate, FarmView
from app.domain.quotas import check_farm_quota, QuotaExceededError
from app.domain.audit import get_audit_logger
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.post("/farms", response_model=FarmView, status_code=status.HTTP_201_CREATED)
def create_farm(
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
    
    use_case = CreateFarmUseCase(db)
    farm = use_case.execute(
        tenant_id=str(membership.tenant_id),
        name=farm_data.name,
        timezone=farm_data.timezone
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
    return FarmView.from_orm(farm)


@router.get("/farms", response_model=List[FarmView])
def list_farms(
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    List all farms for the current tenant.
    """
    use_case = ListFarmsUseCase(db)
    farms = use_case.execute(tenant_id=membership.tenant_id)
    return [FarmView.from_orm(farm) for farm in farms]


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
        
    import httpx
    
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "format": "json",
        "q": q,
        "limit": 5,
        "addressdetails": 1
    }
    headers = {
        "User-Agent": "VivaCampo/1.0 (contact@vivacampo.com)"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("geocode_failed", error=str(e))
            raise HTTPException(status_code=500, detail="Geocoding service unavailable")
