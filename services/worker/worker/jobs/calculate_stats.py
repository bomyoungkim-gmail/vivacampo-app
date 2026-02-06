"""
CALCULATE_STATS Job

Calculates vegetation index statistics for an AOI using TiTiler's
statistics endpoint. This replaces the old approach of downloading
COGs and calculating stats locally.
"""
from __future__ import annotations

import asyncio
import structlog
from sqlalchemy.orm import Session

from worker.application.dtos.calculate_stats import CalculateStatsCommand
from worker.application.use_cases.calculate_stats import CalculateStatsUseCase
from worker.infrastructure.di_container import WorkerContainer

logger = structlog.get_logger()


def calculate_stats_handler(job_id: str, payload: dict, db: Session) -> dict:
    container = WorkerContainer()
    use_case = CalculateStatsUseCase(
        job_repo=container.job_repository(db),
        aoi_repo=container.aoi_geometry_repository(db),
        mosaic_storage=container.mosaic_storage(),
        tiler_provider=container.tiler_stats_provider(),
        observations_repo=container.observations_repository(db),
    )

    command = CalculateStatsCommand(
        job_id=str(job_id),
        tenant_id=payload.get("tenant_id"),
        aoi_id=payload.get("aoi_id"),
        year=payload.get("year"),
        week=payload.get("week"),
        indices=payload.get("indices"),
    )

    return asyncio.run(use_case.execute(command)).model_dump()


def calculate_stats_sync_handler(job_id: str, payload: dict, db: Session) -> dict:
    return calculate_stats_handler(job_id, payload, db)
