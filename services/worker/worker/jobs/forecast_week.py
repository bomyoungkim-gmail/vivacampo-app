"""
FORECAST_WEEK handler - Generate yield forecasts using index-relative method.
Estimates harvest based on historical NDVI patterns.
"""
from __future__ import annotations

import structlog
from sqlalchemy.orm import Session

from worker.application.dtos.forecast_week import ForecastWeekCommand
from worker.application.use_cases.forecast_week import ForecastWeekUseCase
from worker.infrastructure.di_container import WorkerContainer

logger = structlog.get_logger()


async def handle_forecast_week(job: dict, db: Session):
    logger.info("forecast_week_started", job_id=job["id"])

    payload = job.get("payload", {})
    command = ForecastWeekCommand(
        job_id=str(job["id"]),
        tenant_id=job.get("tenant_id"),
        aoi_id=job.get("aoi_id"),
        year=payload.get("year"),
        week=payload.get("week"),
    )

    container = WorkerContainer()
    use_case = ForecastWeekUseCase(
        job_repo=container.job_repository(db),
        season_repo=container.season_repository(db),
        observations_repo=container.forecast_observations_repository(db),
        forecast_repo=container.yield_forecast_repository(db),
    )

    return use_case.execute(command).model_dump()
