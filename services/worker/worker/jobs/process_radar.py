"""PROCESS_RADAR_WEEK job handler."""
from __future__ import annotations

import asyncio
import structlog
from sqlalchemy.orm import Session

from worker.application.dtos.process_radar import ProcessRadarCommand
from worker.application.use_cases.process_radar import ProcessRadarUseCase
from worker.infrastructure.di_container import WorkerContainer

logger = structlog.get_logger()


def process_radar_week_handler(job_id: str, payload: dict, db: Session):
    logger.info("process_radar_week_start", job_id=job_id)

    container = WorkerContainer()
    use_case = ProcessRadarUseCase(
        job_repo=container.job_repository(db),
        aoi_repo=container.aoi_geometry_repository(db),
        radar_provider=container.radar_provider(),
        storage=container.object_storage(),
        radar_repo=container.radar_repository(db),
    )

    command = ProcessRadarCommand(
        job_id=str(job_id),
        tenant_id=payload.get("tenant_id"),
        aoi_id=payload.get("aoi_id"),
        year=payload.get("year"),
        week=payload.get("week"),
    )

    return asyncio.run(use_case.execute(command)).model_dump()
