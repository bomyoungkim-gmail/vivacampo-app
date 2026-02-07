"""Ports for weather data retrieval and AOI geometry lookup."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Iterable


class WeatherProvider(ABC):
    @abstractmethod
    async def fetch_history(
        self, *, lat: float, lon: float, start_date: date, end_date: date
    ) -> list[dict]:
        """Fetch weather history data for a date range (normalized list)."""
        raise NotImplementedError


class WeatherRepository(ABC):
    @abstractmethod
    def save_batch(self, *, tenant_id: str, aoi_id: str, records: Iterable[dict]) -> None:
        """Persist weather records."""
        raise NotImplementedError


class AoiGeometryRepository(ABC):
    @abstractmethod
    def get_geometry(self, *, tenant_id: str, aoi_id: str) -> dict | None:
        """Return AOI geometry as GeoJSON-like dict."""
        raise NotImplementedError
