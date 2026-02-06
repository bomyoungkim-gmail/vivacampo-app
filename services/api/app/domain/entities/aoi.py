"""
AOI (Area of Interest) domain entity.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from app.domain.base import DomainEntity
from app.domain.value_objects.area_hectares import AreaHectares
from app.domain.value_objects.geometry_wkt import GeometryWkt
from app.domain.value_objects.tenant_id import TenantId


class AOI(DomainEntity):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: TenantId
    farm_id: UUID
    name: str = Field(min_length=3, max_length=200)
    use_type: str = Field(min_length=3, max_length=20)
    status: str = Field(default="ACTIVE", min_length=3, max_length=20)
    geometry_wkt: GeometryWkt
    area_hectares: AreaHectares
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    crop_type: Optional[str] = Field(default=None, max_length=50)
    planting_date: Optional[datetime] = None

    @field_validator("use_type")
    @classmethod
    def validate_use_type(cls, v: str) -> str:
        allowed = {"PASTURE", "CROP", "TIMBER"}
        if v not in allowed:
            raise ValueError(f"Invalid use_type: {v}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"ACTIVE", "INACTIVE", "DELETED"}
        if v not in allowed:
            raise ValueError(f"Invalid status: {v}")
        return v

    def update_geometry(self, new_geometry: GeometryWkt, new_area: AreaHectares) -> None:
        self.geometry_wkt = new_geometry
        self.area_hectares = new_area
        self.updated_at = datetime.utcnow()
