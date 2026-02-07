"""AOI DTOs for application layer."""
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

from pydantic import Field

from app.domain.base import ImmutableDTO
from app.domain.value_objects.tenant_id import TenantId


class CreateAoiCommand(ImmutableDTO):
    tenant_id: TenantId
    parent_aoi_id: UUID | None = None
    farm_id: UUID
    name: str = Field(min_length=1, max_length=200)
    use_type: str
    geometry_wkt: str


class ListAoisCommand(ImmutableDTO):
    tenant_id: TenantId
    farm_id: Optional[UUID] = None
    status: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=500)


class AoiResult(ImmutableDTO):
    id: UUID
    tenant_id: UUID
    parent_aoi_id: UUID | None = None
    farm_id: UUID
    name: str
    use_type: str
    status: str
    area_ha: float
    geometry: str
    created_at: datetime


class SimulateSplitCommand(ImmutableDTO):
    tenant_id: TenantId
    geometry_wkt: str
    mode: Literal["voronoi", "grid"]
    target_count: int
    max_area_ha: float = 2000


class SplitPolygonResult(ImmutableDTO):
    geometry_wkt: str
    area_ha: float


class SimulateSplitResult(ImmutableDTO):
    polygons: list[SplitPolygonResult]
    warnings: list[str]


class SplitPolygonInput(ImmutableDTO):
    geometry_wkt: str
    name: str | None = None


class SplitAoiCommand(ImmutableDTO):
    tenant_id: TenantId
    parent_aoi_id: UUID
    polygons: list[SplitPolygonInput]
    max_area_ha: float = 2000
    idempotency_key: str | None = None


class SplitAoiResult(ImmutableDTO):
    created_ids: list[UUID]
    idempotent: bool = False


class AoiStatusCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_ids: list[UUID]


class AoiStatusItem(ImmutableDTO):
    aoi_id: UUID
    is_processing: bool
    job_status: str | None = None
    job_type: str | None = None
    updated_at: datetime | None = None


class AoiStatusResult(ImmutableDTO):
    items: list[AoiStatusItem]


class FieldCalibrationCreateCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID
    observed_date: str
    metric_type: str
    value: float
    unit: str = "kg_ha"
    source: str = "MANUAL"


class FieldCalibrationResult(ImmutableDTO):
    id: UUID
    aoi_id: UUID
    observed_date: str
    metric_type: str
    value: float
    unit: str
    source: str


class CalibrationCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID
    metric_type: str


class CalibrationResult(ImmutableDTO):
    r2: float
    coefficients: dict
    sample_size: int


class PredictionCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID
    metric_type: str


class PredictionResult(ImmutableDTO):
    p10: float
    p50: float
    p90: float
    unit: str
    confidence: float
    source: str


class FieldFeedbackCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID
    feedback_type: str
    message: str
    created_by_membership_id: UUID | None


class FieldFeedbackResult(ImmutableDTO):
    id: UUID
