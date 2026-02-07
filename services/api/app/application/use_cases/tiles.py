"""Tiles use cases."""
from __future__ import annotations

from datetime import timedelta

import httpx
import structlog

from app.application.decorators import require_tenant
from app.application.dtos.tiles import (
    TileExportCommand,
    TileExportResult,
    TileExportStatusCommand,
    TileJsonCommand,
    TileRedirect,
    TileRequestCommand,
)
from app.application.tiles_config import build_tiler_url, get_current_iso_week, get_mosaic_url, EXPRESSIONS
from app.domain.ports.aoi_spatial_repository import IAoiSpatialRepository
from app.domain.ports.object_storage import IObjectStorage

logger = structlog.get_logger()


class GetAoiTileUseCase:
    def __init__(self, repo: IAoiSpatialRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: TileRequestCommand) -> TileRedirect:
        exists = await self.repo.exists(command.tenant_id, command.aoi_id)
        if not exists:
            raise ValueError("AOI_NOT_FOUND")

        index = command.index.lower()
        if index not in EXPRESSIONS:
            raise ValueError("INVALID_INDEX")

        if not command.year or not command.week:
            year, week = get_current_iso_week()
        else:
            year, week = command.year, command.week

        tiler_url = build_tiler_url(command.z, command.x, command.y, index, year, week)
        return TileRedirect(url=tiler_url, index=index, year=year, week=week)


class GetAoiTileJsonUseCase:
    def __init__(self, repo: IAoiSpatialRepository, api_base_url: str, cdn_enabled: bool, cdn_tiles_url: str | None):
        self.repo = repo
        self.api_base_url = api_base_url
        self.cdn_enabled = cdn_enabled
        self.cdn_tiles_url = cdn_tiles_url

    @require_tenant
    async def execute(self, command: TileJsonCommand) -> dict:
        meta = await self.repo.get_tilejson_metadata(command.tenant_id, command.aoi_id)
        if not meta:
            raise ValueError("AOI_NOT_FOUND")

        if not command.year or not command.week:
            year, week = get_current_iso_week()
        else:
            year, week = command.year, command.week

        index = command.index.lower()
        if index not in EXPRESSIONS:
            index = "ndvi"

        if self.cdn_enabled and self.cdn_tiles_url:
            base_url = self.cdn_tiles_url
        else:
            base_url = self.api_base_url

        tile_url = (
            f"{base_url}/v1/tiles/aois/{command.aoi_id}/{{z}}/{{x}}/{{y}}.png"
            f"?index={index}&year={year}&week={week}"
        )

        return {
            "tilejson": "3.0.0",
            "name": f"{meta['name']} - {index.upper()}",
            "description": f"Vegetation index {index.upper()} for {meta['name']}, {year} week {week}",
            "version": "1.0.0",
            "attribution": "VivaCampo - Sentinel-2 via Planetary Computer",
            "tiles": [tile_url],
            "minzoom": 8,
            "maxzoom": 16,
            "bounds": [meta["minx"], meta["miny"], meta["maxx"], meta["maxy"]],
            "center": [meta["cx"], meta["cy"], 12],
        }


class RequestAoiExportUseCase:
    def __init__(self, repo: IAoiSpatialRepository, storage: IObjectStorage):
        self.repo = repo
        self.storage = storage

    @require_tenant
    async def execute(self, command: TileExportCommand) -> TileExportResult:
        meta = await self.repo.get_tilejson_metadata(command.tenant_id, command.aoi_id)
        if not meta:
            raise ValueError("AOI_NOT_FOUND")

        if not command.year or not command.week:
            year, week = get_current_iso_week()
        else:
            year, week = command.year, command.week

        index = command.index.lower()
        if index not in EXPRESSIONS:
            raise ValueError("INVALID_INDEX")

        export_key = f"exports/{command.tenant_id.value}/{command.aoi_id}/{index}-{year}-w{week:02d}.tif"

        if await self.storage.exists(export_key):
            presigned_url = await self.storage.generate_presigned_url(export_key, timedelta(hours=24))
            return TileExportResult(
                status="ready",
                download_url=presigned_url,
                filename=f"{meta['name']}-{index}-{year}-w{week:02d}.tif",
                expires_in=86400,
                cached=True,
            )

        return TileExportResult(
            status="processing",
            message="COG export is being generated. Check back in 1-2 minutes.",
            export_key=export_key,
            filename=f"{meta['name']}-{index}-{year}-w{week:02d}.tif",
        )


class GetAoiExportStatusUseCase:
    def __init__(self, storage: IObjectStorage):
        self.storage = storage

    @require_tenant
    async def execute(self, command: TileExportStatusCommand) -> TileExportResult:
        if not command.year or not command.week:
            year, week = get_current_iso_week()
        else:
            year, week = command.year, command.week

        index = command.index.lower()
        export_key = f"exports/{command.tenant_id.value}/{command.aoi_id}/{index}-{year}-w{week:02d}.tif"

        if await self.storage.exists(export_key):
            presigned_url = await self.storage.generate_presigned_url(export_key, timedelta(hours=24))
            return TileExportResult(
                status="ready",
                download_url=presigned_url,
                expires_in=86400,
            )

        return TileExportResult(
            status="processing",
            message="Export is still being generated or has not been requested.",
        )


class GenerateAoiExportUseCase:
    def __init__(self, repo: IAoiSpatialRepository, storage: IObjectStorage, tiler_url: str):
        self.repo = repo
        self.storage = storage
        self.tiler_url = tiler_url

    async def execute(
        self,
        tenant_id,
        aoi_id,
        index,
        year,
        week,
        export_key,
    ) -> None:
        geometry = await self.repo.get_geojson(tenant_id, aoi_id)
        if not geometry:
            logger.error("cog_export_aoi_not_found", aoi_id=str(aoi_id))
            return

        mosaic_url = get_mosaic_url(year, week)
        expression = EXPRESSIONS.get(index)

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.tiler_url}/mosaic/crop",
                params={
                    "url": mosaic_url,
                    "expression": expression,
                    "format": "tif",
                },
                json=geometry,
            )

        if response.status_code != 200:
            logger.error(
                "cog_export_tiler_error",
                status_code=response.status_code,
                response=response.text[:500],
            )
            return

        await self.storage.upload(export_key, response.content, content_type="image/tiff")
        logger.info(
            "cog_export_complete",
            aoi_id=str(aoi_id),
            export_key=export_key,
            size_bytes=len(response.content),
        )
