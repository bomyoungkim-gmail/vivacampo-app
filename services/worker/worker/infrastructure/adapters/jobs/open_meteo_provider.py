"""Open-Meteo provider adapter."""
from __future__ import annotations

import asyncio
from datetime import date

import requests
import structlog

from worker.domain.ports.weather_provider import WeatherProvider

logger = structlog.get_logger()


class OpenMeteoProvider(WeatherProvider):
    def __init__(self, base_url: str = "https://archive-api.open-meteo.com/v1/archive") -> None:
        self._base_url = base_url

    async def fetch_history(self, *, lat: float, lon: float, start_date: date, end_date: date) -> dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,et0_fao_evapotranspiration",
            "timezone": "auto",
        }
        logger.info("fetching_open_meteo", params=params)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: requests.get(self._base_url, params=params))
        response.raise_for_status()
        return response.json()
