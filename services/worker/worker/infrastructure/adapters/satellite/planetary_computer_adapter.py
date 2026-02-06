"""Planetary Computer adapter implementing ISatelliteProvider."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
import structlog

from worker.domain.ports.satellite_provider import ISatelliteProvider, SatelliteScene
from worker.pipeline.stac_client import get_stac_client

logger = structlog.get_logger()


class _SatelliteSceneSchema(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    id: str
    datetime: str
    cloud_cover: float = Field(ge=0.0, le=100.0)
    platform: str
    collection: Optional[str] = None
    bbox: List[float] = Field(min_length=4, max_length=4)
    geometry: Dict[str, Any]
    assets: Dict[str, Optional[str]]

    @field_validator("datetime")
    @classmethod
    def validate_datetime(cls, v: str) -> str:
        # ISO-8601 string required
        datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v


class PlanetaryComputerAdapter(ISatelliteProvider):
    """Adapter over existing STAC client for Planetary Computer."""

    @property
    def provider_name(self) -> str:
        return "planetary_computer"

    async def search_scenes(
        self,
        geometry: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        collections: Optional[List[str]] = None,
        max_cloud_cover: float = 60.0,
    ) -> List[SatelliteScene]:
        stac = get_stac_client()
        raw_items = await stac.search_scenes(
            aoi_geom=geometry,
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=max_cloud_cover,
            collections=collections,
        )

        scenes: List[SatelliteScene] = []
        for item in raw_items:
            if item.get("cloud_cover") is None:
                item = {**item, "cloud_cover": 0.0}
            try:
                validated = _SatelliteSceneSchema(**item)
            except Exception as exc:
                logger.warning("satellite_scene_invalid", exc_info=exc, item_id=item.get("id"))
                continue

            scenes.append(
                SatelliteScene(
                    id=validated.id,
                    datetime=datetime.fromisoformat(validated.datetime.replace("Z", "+00:00")),
                    cloud_cover=validated.cloud_cover,
                    platform=validated.platform,
                    collection=validated.collection or "unknown",
                    bbox=validated.bbox,
                    geometry=validated.geometry,
                    assets=validated.assets,
                )
            )

        return scenes

    async def download_band(self, asset_href: str, geometry: Dict[str, Any], output_path: str) -> str:
        stac = get_stac_client()
        return await stac.download_band(asset_href=asset_href, geometry=geometry, output_path=output_path)

    async def health_check(self) -> bool:
        # Simple health check by ensuring client can be created
        try:
            _ = get_stac_client()
            return True
        except Exception as exc:
            logger.warning("planetary_computer_health_failed", exc_info=exc)
            return False
