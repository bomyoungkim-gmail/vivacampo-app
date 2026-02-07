"""Open-Meteo provider adapter."""
from __future__ import annotations

from datetime import date

import structlog

from worker.domain.ports.weather_provider import WeatherProvider
from worker.pipeline.providers.registry import get_weather_provider

logger = structlog.get_logger()


class OpenMeteoProvider(WeatherProvider):
    def __init__(self, base_url: str = "https://archive-api.open-meteo.com/v1/archive") -> None:
        self._base_url = base_url

    async def fetch_history(self, *, lat: float, lon: float, start_date: date, end_date: date) -> list[dict]:
        logger.info("fetching_open_meteo", lat=lat, lon=lon, start_date=start_date, end_date=end_date)
        provider = get_weather_provider()
        return await provider.fetch_history(
            lat=lat,
            lon=lon,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            timezone="auto",
        )
