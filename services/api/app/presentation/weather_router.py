
from fastapi import APIRouter, Depends, status
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.auth.dependencies import get_current_membership, CurrentMembership, require_role, get_current_tenant_id
from app.application.dtos.weather import WeatherHistoryCommand, WeatherSyncCommand
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.di_container import ApiContainer, get_container

router = APIRouter(responses=DEFAULT_ERROR_RESPONSES, dependencies=[Depends(get_current_tenant_id)])

@router.get("/aois/{aoi_id}/weather/history", response_model=List[dict])
async def get_weather_history(
    aoi_id: UUID,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 365,
    membership: CurrentMembership = Depends(get_current_membership),
    container: ApiContainer = Depends(get_container)
):
    """
    Get historical weather data (Precipitation, Temperature, ET0).
    """
    use_case = container.weather_history_use_case()
    return await use_case.execute(
        WeatherHistoryCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            aoi_id=aoi_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    )

@router.post("/aois/{aoi_id}/weather/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_weather_data(
    aoi_id: UUID,
    membership: CurrentMembership = Depends(require_role("EDITOR")),
    container: ApiContainer = Depends(get_container)
):
    """
    Trigger a job to fetch/update weather data from Open-Meteo.
    """
    use_case = container.request_weather_sync_use_case()
    result = await use_case.execute(
        WeatherSyncCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            aoi_id=aoi_id,
        )
    )
    return {"message": result.message, "job_id": result.job_id}
