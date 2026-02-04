"""
Nitrogen deficiency detection API.
Algorithm: High NDVI (>0.7) + Low NDRE (<0.5) + Low RECI (<1.5) = DEFICIENT
"""
from typing import Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.nitrogen import GetNitrogenStatusUseCase
from app.auth.dependencies import CurrentMembership, get_current_membership
from app.config import settings
from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


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
    base_url = settings.API_BASE_URL or "http://localhost:8000"
    use_case = GetNitrogenStatusUseCase(db)
    result = use_case.execute(str(membership.tenant_id), str(aoi_id), base_url)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vegetation data found",
        )

    return NitrogenStatus(**result)
