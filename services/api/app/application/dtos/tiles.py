"""Tiles DTOs."""
from datetime import date
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.domain.base import ImmutableDTO
from app.domain.value_objects.tenant_id import TenantId


class TileRequestCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID
    z: int
    x: int
    y: int
    index: str = Field(default="ndvi")
    year: Optional[int] = None
    week: Optional[int] = None


class TileJsonCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID
    index: str = Field(default="ndvi")
    year: Optional[int] = None
    week: Optional[int] = None


class TileExportCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID
    index: str = Field(default="ndvi")
    year: Optional[int] = None
    week: Optional[int] = None


class TileExportStatusCommand(ImmutableDTO):
    tenant_id: TenantId
    aoi_id: UUID
    index: str = Field(default="ndvi")
    year: Optional[int] = None
    week: Optional[int] = None


class TileRedirect(ImmutableDTO):
    url: str
    index: str
    year: int
    week: int


class TileExportResult(ImmutableDTO):
    status: str
    filename: Optional[str] = None
    export_key: Optional[str] = None
    download_url: Optional[str] = None
    expires_in: Optional[int] = None
    cached: Optional[bool] = None
    message: Optional[str] = None
