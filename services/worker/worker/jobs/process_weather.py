"""PROCESS_WEATHER handler."""
from __future__ import annotations

import asyncio
import structlog
from sqlalchemy.orm import Session

from worker.application.dtos.process_weather import ProcessWeatherCommand
from worker.application.use_cases.process_weather import ProcessWeatherUseCase, clamp_date_range
from worker.infrastructure.di_container import WorkerContainer

logger = structlog.get_logger()


def process_weather_history_handler(job_id: str, payload: dict, db: Session):
    container = WorkerContainer()
    use_case = ProcessWeatherUseCase(
        job_repo=container.job_repository(db),
        aoi_repo=container.aoi_geometry_repository(db),
        weather_repo=container.weather_repository(db),
        weather_provider=container.weather_provider(),
    )

    command = ProcessWeatherCommand(
        job_id=str(job_id),
        tenant_id=payload.get("tenant_id"),
        aoi_id=payload.get("aoi_id"),
        start_date=payload.get("start_date"),
        end_date=payload.get("end_date"),
    )

    return asyncio.run(use_case.execute(command)).model_dump()
