"""Nitrogen DTOs for application layer."""
from typing import Optional

from app.domain.base import ImmutableDTO
from app.domain.value_objects.tenant_id import TenantId


class GetNitrogenStatusCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: str
    base_url: str


class NitrogenStatusResult(ImmutableDTO):
    status: str
    confidence: float
    ndvi_mean: Optional[float] = None
    ndre_mean: Optional[float] = None
    reci_mean: Optional[float] = None
    recommendation: str
    zone_map_url: Optional[str] = None
