"""
Nitrogen deficiency detection API.
Algorithm: High NDVI (>0.7) + Low NDRE (<0.5) + Low RECI (<1.5) = DEFICIENT
"""
from typing import Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.dtos.nitrogen import GetNitrogenStatusCommand
from app.application.use_cases.nitrogen import GetNitrogenStatusUseCase
from app.auth.dependencies import CurrentMembership, get_current_membership, get_current_tenant_id
from app.config import settings
from app.database import get_db
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.di_container import ApiContainer

logger = logging.getLogger(__name__)
router = APIRouter(responses=DEFAULT_ERROR_RESPONSES, dependencies=[Depends(get_current_tenant_id)])


class NitrogenStatus(BaseModel):
    status: str  # DEFICIENT, ADEQUATE, UNKNOWN
    confidence: float
    ndvi_mean: Optional[float] = None
    ndre_mean: Optional[float] = None
    reci_mean: Optional[float] = None
    recommendation: str
    zone_map_url: Optional[str] = None


@router.get("/aois/{aoi_id}/nitrogen/status", response_model=NitrogenStatus)
def get_nitrogen_status(
    aoi_id: UUID,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
):
    """Get nitrogen deficiency status for an AOI."""
    base_url = settings.api_base_url or "http://localhost:8000"
    container = ApiContainer()
    use_case = container.nitrogen_use_case(db)
    result = use_case.execute(
        GetNitrogenStatusCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            aoi_id=str(aoi_id),
            base_url=base_url,
        )
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vegetation data found",
        )

    return NitrogenStatus(**result.model_dump())