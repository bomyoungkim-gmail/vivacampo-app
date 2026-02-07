"""
Abstract base for satellite and weather data providers.
All providers must implement this interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np


class SatelliteDataProvider(ABC):
    """
    Interface that every satellite data provider must implement.

    Responsibilities:
    - Search satellite scenes (search_scenes)
    - Sign URLs for download (sign_url)
    - Download and clip bands (download_and_clip_band)

    Not included:
    - Index calculation (IndexCalculator)
    - Weather data (WeatherDataProvider)
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique provider name (e.g. 'planetary_computer')."""
        ...

    @property
    @abstractmethod
    def supported_collections(self) -> List[str]:
        """Collections supported by this provider."""
        ...

    @abstractmethod
    async def search_scenes(
        self,
        aoi_geom: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 60.0,
        collections: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for satellite scenes covering the AOI.

        Returns standardized scene metadata:
        {
          "id": str,
          "datetime": str (ISO),
          "cloud_cover": float,
          "platform": str,
          "assets": { ... },
          "bbox": List[float],
          "geometry": Dict[str, Any],
        }
        """
        ...

    @abstractmethod
    async def download_and_clip_band(
        self,
        asset_href: str,
        aoi_geom: Dict[str, Any],
        output_path: str,
    ) -> np.ndarray:
        """
        Download asset, clip by AOI and save as GeoTIFF.
        Must sign URL internally if required.
        Returns array for first band.
        """
        ...

    @abstractmethod
    def sign_url(self, href: str) -> str:
        """Sign URL if required, otherwise return original."""
        ...

    @abstractmethod
    async def search_raw_items(
        self,
        bbox: List[float],
        start_date: datetime,
        end_date: datetime,
        max_cloud_cover: float = 60.0,
        collections: Optional[List[str]] = None,
        max_items: int = 2000,
    ):
        """
        Search raw STAC items (pystac.Item) for MosaicJSON builder.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Quick availability check (<= 5s)."""
        ...


class WeatherDataProvider(ABC):
    """Interface for weather data providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    async def fetch_history(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        timezone: str = "auto",
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical weather data.

        Returns standardized list:
        {
          "date": "YYYY-MM-DD",
          "temp_max": float,
          "temp_min": float,
          "precip_sum": float,
          "et0_fao": float,
        }
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...
