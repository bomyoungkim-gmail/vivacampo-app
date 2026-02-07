from fastapi import APIRouter, Depends
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from typing import List, Optional
from uuid import UUID

from app.auth.dependencies import get_current_membership, CurrentMembership, get_current_tenant_id
from app.infrastructure.s3_client import presign_row_s3_fields
from app.application.dtos.radar import RadarHistoryCommand
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.di_container import ApiContainer, get_container

router = APIRouter(responses=DEFAULT_ERROR_RESPONSES, dependencies=[Depends(get_current_tenant_id)])

@router.get("/aois/{aoi_id}/radar/history", response_model=List[dict])
async def get_radar_history(
    aoi_id: UUID,
    year: Optional[int] = None,
    limit: int = 52,
    membership: CurrentMembership = Depends(get_current_membership),
    container: ApiContainer = Depends(get_container)
):
    """
    Get historical Radar (Sentinel-1) data (RVI, Ratio).
    """
    use_case = container.radar_history_use_case()
    history = await use_case.execute(
        RadarHistoryCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            aoi_id=aoi_id,
            year=year,
            limit=limit,
        )
    )
    s3_fields = ["rvi_s3_uri", "ratio_s3_uri"]
    return [presign_row_s3_fields(row, s3_fields) for row in history]
