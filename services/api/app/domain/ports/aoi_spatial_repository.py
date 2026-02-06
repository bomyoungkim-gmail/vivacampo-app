"""AOI spatial repository port for tile metadata and geometry."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.value_objects.tenant_id import TenantId


class IAoiSpatialRepository(ABC):
    @abstractmethod
    async def exists(self, tenant_id: TenantId, aoi_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_tilejson_metadata(self, tenant_id: TenantId, aoi_id: UUID) -> Optional[dict]:
        """Return name, bounds, center for TileJSON."""
        raise NotImplementedError

    @abstractmethod
    async def get_geojson(self, tenant_id: TenantId, aoi_id: UUID) -> Optional[dict]:
        """Return AOI geometry as GeoJSON dict."""
        raise NotImplementedError
