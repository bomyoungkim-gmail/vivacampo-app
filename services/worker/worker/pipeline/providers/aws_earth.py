"""
AWS Earth Search STAC provider.
"""
from __future__ import annotations

import asyncio
import os
import socket
import tempfile
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_geom
from shapely.geometry import mapping, shape
import structlog
from pystac_client import Client
from pystac_client.stac_api_io import StacApiIO
from pystac_client.exceptions import APIError
from urllib3 import Retry
from requests.exceptions import RequestException, Timeout as RequestsTimeout
from tenacity import Retrying, stop_after_attempt, wait_exponential, retry_if_exception_type

from worker.pipeline.providers.base import SatelliteDataProvider

logger = structlog.get_logger()


class AWSEarthSearchProvider(SatelliteDataProvider):
    """AWS Earth Search STAC provider (Element84)."""

    CATALOG_URL = "https://earth-search.aws.element84.com/v1"

    BAND_MAPPING = {
        "sentinel-2-l2a": {
            "red": "B04",
            "green": "B03",
            "blue": "B02",
            "nir": "B08",
            "swir": "B11",
            "swir2": "B12",
            "rededge": "B05",
            "scl": "SCL",
        },
        "sentinel-1-grd": {
            "vv": "vv",
            "vh": "vh",
        },
    }

    def __init__(self, catalog_url: Optional[str] = None):
        self._catalog_url = catalog_url or self.CATALOG_URL
        self._client = None
        self.search_limit = 50
        self.search_max_items = 100
        self.search_timeout = (5, 60)
        self.search_max_retries = 5

    @property
    def provider_name(self) -> str:
        return "aws_earth"

    @property
    def supported_collections(self) -> List[str]:
        return ["sentinel-2-l2a", "sentinel-1-grd"]

    def _build_stac_io(self) -> StacApiIO:
        retry = Retry(
            total=self.search_max_retries,
            backoff_factor=1,
            status_forcelist=[502, 503, 504],
            allowed_methods=None,
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        return StacApiIO(max_retries=retry, timeout=self.search_timeout)

    def _get_client(self):
        if self._client is None:
            stac_io = self._build_stac_io()
            self._client = Client.open(self._catalog_url, stac_io=stac_io)
            logger.info("provider_initialized", provider=self.provider_name, catalog=self._catalog_url)
        return self._client

    async def search_scenes(
        self,
        aoi_geom: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 60.0,
        collections: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        if collections is None:
            collections = ["sentinel-2-l2a"]

        client = self._get_client()

        try:
            bounds = shape(aoi_geom).bounds
        except Exception:
            bounds = None

        query = {}
        if "sentinel-2-l2a" in collections:
            query["eo:cloud_cover"] = {"lt": max_cloud_cover}

        search_kwargs: Dict[str, Any] = {
            "collections": collections,
            "datetime": f"{start_date.isoformat()}/{end_date.isoformat()}",
            "query": query,
            "limit": self.search_limit,
            "max_items": self.search_max_items,
        }
        if bounds:
            search_kwargs["bbox"] = list(bounds)
        else:
            search_kwargs["intersects"] = aoi_geom

        retryer = Retrying(
            stop=stop_after_attempt(4),
            wait=wait_exponential(multiplier=1, min=1, max=15),
            retry=retry_if_exception_type((APIError, RequestException, RequestsTimeout)),
            reraise=True,
        )
        for attempt in retryer:
            with attempt:
                search = client.search(**search_kwargs)
                items = list(search.items())

        scenes: List[Dict[str, Any]] = []
        for item in items:
            collection_id = item.collection_id
            band_map = self.BAND_MAPPING.get(collection_id, {})

            assets: Dict[str, Optional[str]] = {}
            for standard_name, pc_name in band_map.items():
                asset = item.assets.get(pc_name)
                assets[standard_name] = asset.href if asset else None

            scenes.append(
                {
                    "id": item.id,
                    "datetime": item.datetime.isoformat(),
                    "cloud_cover": item.properties.get("eo:cloud_cover", 0),
                    "platform": item.properties.get("platform", "unknown"),
                    "assets": assets,
                    "bbox": item.bbox,
                    "geometry": mapping(shape(item.geometry)),
                }
            )

        return scenes

    async def search_raw_items(
        self,
        bbox: List[float],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 60.0,
        collections: Optional[List[str]] = None,
        max_items: int = 2000,
    ):
        if collections is None:
            collections = ["sentinel-2-l2a"]

        client = self._get_client()

        query = {}
        if "sentinel-2-l2a" in collections:
            query["eo:cloud_cover"] = {"lt": max_cloud_cover}

        search = client.search(
            collections=collections,
            bbox=bbox,
            datetime=f"{start_date}/{end_date}",
            query=query if query else None,
            max_items=max_items,
        )
        return list(search.items())

    def sign_url(self, href: str) -> str:
        return href

    async def download_and_clip_band(
        self,
        asset_href: str,
        aoi_geom: Dict[str, Any],
        output_path: str,
    ) -> np.ndarray:
        local_path = None
        try:
            local_path = await asyncio.to_thread(self._download_asset, asset_href)
            with rasterio.open(local_path) as src:
                aoi_projected = transform_geom("EPSG:4326", src.crs, aoi_geom)
                geom = [shape(aoi_projected)]
                out_image, out_transform = mask(src, geom, crop=True)
                out_meta = src.meta.copy()
                out_meta.update(
                    {
                        "driver": "GTiff",
                        "height": out_image.shape[1],
                        "width": out_image.shape[2],
                        "transform": out_transform,
                    }
                )
                with rasterio.open(output_path, "w", **out_meta) as dest:
                    dest.write(out_image)
                return out_image[0]
        finally:
            if local_path and os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except Exception:
                    pass

    def _download_asset(self, href: str) -> str:
        import urllib.request

        signed_href = self.sign_url(href)
        max_attempts = 5

        for attempt in range(max_attempts):
            try:
                socket.setdefaulttimeout(30)
                fd, temp_path = tempfile.mkstemp(suffix=".tif")
                os.close(fd)

                with urllib.request.urlopen(signed_href) as response:
                    with open(temp_path, "wb") as f:
                        while True:
                            chunk = response.read(16 * 1024)
                            if not chunk:
                                break
                            f.write(chunk)

                return temp_path
            except Exception as exc:
                logger.error("download_error", provider=self.provider_name, error=str(exc), attempt=attempt + 1)
                if attempt < max_attempts - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise

    async def health_check(self) -> bool:
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self._catalog_url, timeout=5) as resp:
                    return resp.status == 200
        except Exception:
            return False
