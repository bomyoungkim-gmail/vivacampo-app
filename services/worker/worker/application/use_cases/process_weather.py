"""Use case for PROCESS_WEATHER job."""
from __future__ import annotations

from datetime import date, datetime, timedelta

import structlog
from shapely.geometry import shape

from worker.application.dtos.process_weather import ProcessWeatherCommand, ProcessWeatherResult
from worker.domain.ports.job_repository import JobRepository
from worker.domain.ports.weather_provider import AoiGeometryRepository, WeatherProvider, WeatherRepository

logger = structlog.get_logger()


class ProcessWeatherUseCase:
    def __init__(
        self,
        job_repo: JobRepository,
        aoi_repo: AoiGeometryRepository,
        weather_repo: WeatherRepository,
        weather_provider: WeatherProvider,
    ) -> None:
        self._job_repo = job_repo
        self._aoi_repo = aoi_repo
        self._weather_repo = weather_repo
        self._weather_provider = weather_provider

    async def execute(self, command: ProcessWeatherCommand) -> ProcessWeatherResult:
        logger.info("process_weather_start", job_id=command.job_id)
        self._job_repo.mark_status(command.job_id, "RUNNING")
        self._job_repo.commit()

        try:
            start_date, end_date, did_clamp = _resolve_date_range(command)
            geometry = self._aoi_repo.get_geometry(tenant_id=command.tenant_id, aoi_id=command.aoi_id)
            if not geometry:
                raise ValueError("AOI Geometry not found")

            centroid = shape(geometry).centroid
            lat, lon = centroid.y, centroid.x

            data = await self._weather_provider.fetch_history(
                lat=lat,
                lon=lon,
                start_date=start_date,
                end_date=end_date,
            )

            records = _normalize_records(data)
            self._weather_repo.save_batch(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
                records=records,
            )

            self._job_repo.mark_status(command.job_id, "DONE")
            self._job_repo.commit()

            return ProcessWeatherResult(
                status="DONE",
                records_saved=len(records),
                clamped=did_clamp,
            )
        except Exception as exc:
            logger.error("process_weather_failed", job_id=command.job_id, error=str(exc), exc_info=True)
            self._job_repo.mark_status(command.job_id, "FAILED", error_message=str(exc))
            self._job_repo.commit()
            raise


def _resolve_date_range(command: ProcessWeatherCommand) -> tuple[date, date, bool]:
    end_date = command.end_date or datetime.now().date()
    start_date = command.start_date or end_date - timedelta(days=365 * 10)
    return clamp_date_range(start_date, end_date)


def clamp_date_range(start_date: date, end_date: date, today: date | None = None) -> tuple[date, date, bool]:
    """Clamp the date range to avoid future end dates (Open-Meteo archive rejects)."""
    today = today or datetime.now().date()
    did_clamp = False

    if end_date > today:
        end_date = today
        did_clamp = True

    if start_date > end_date:
        start_date = end_date
        did_clamp = True

    return start_date, end_date, did_clamp


def _normalize_records(payload: dict) -> list[dict]:
    daily = payload.get("daily", {}) if payload else {}
    dates = daily.get("time", [])
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])
    et0 = daily.get("et0_fao_evapotranspiration", [])

    records = []
    for i, date_str in enumerate(dates):
        records.append({
            "date": date_str,
            "temp_max": temp_max[i] if i < len(temp_max) and temp_max[i] is not None else 0,
            "temp_min": temp_min[i] if i < len(temp_min) and temp_min[i] is not None else 0,
            "precip_sum": precip[i] if i < len(precip) and precip[i] is not None else 0,
            "et0_fao": et0[i] if i < len(et0) and et0[i] is not None else 0,
        })
    return records
