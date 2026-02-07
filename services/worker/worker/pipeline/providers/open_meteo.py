"""
Open-Meteo weather provider.
"""
from __future__ import annotations

from typing import Any, Dict, List

import aiohttp
import structlog

from worker.pipeline.providers.base import WeatherDataProvider

logger = structlog.get_logger()


class OpenMeteoProvider(WeatherDataProvider):
    """Weather provider backed by Open-Meteo archive API."""

    @property
    def provider_name(self) -> str:
        return "open_meteo"

    async def fetch_history(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        timezone: str = "auto",
    ) -> List[Dict[str, Any]]:
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "et0_fao_evapotranspiration",
            ],
            "timezone": timezone,
        }

        async with aiohttp.ClientSession() as session:
            logger.info(
                "open_meteo_request",
                lat=lat,
                lon=lon,
                start_date=start_date,
                end_date=end_date,
            )
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.error("open_meteo_failed", status=resp.status, text=await resp.text())
                    return []

                data = await resp.json()
                daily = data.get("daily", {})
                results: List[Dict[str, Any]] = []
                dates = daily.get("time", [])
                for i, day in enumerate(dates):
                    results.append(
                        {
                            "date": day,
                            "temp_max": daily["temperature_2m_max"][i],
                            "temp_min": daily["temperature_2m_min"][i],
                            "precip_sum": daily["precipitation_sum"][i],
                            "et0_fao": daily["et0_fao_evapotranspiration"][i],
                        }
                    )
                logger.info("open_meteo_response", days=len(results))
                return results

    async def health_check(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://archive-api.open-meteo.com/v1/archive", timeout=5) as resp:
                    return resp.status == 200
        except Exception:
            return False
