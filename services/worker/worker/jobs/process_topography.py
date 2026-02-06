"""PROCESS_TOPOGRAPHY job handler."""
from __future__ import annotations

import asyncio
import structlog
from sqlalchemy.orm import Session

from worker.application.dtos.process_topography import ProcessTopographyCommand
from worker.application.use_cases.process_topography import ProcessTopographyUseCase
from worker.infrastructure.di_container import WorkerContainer

logger = structlog.get_logger()


def process_topography_handler(job_id: str, payload: dict, db: Session):
    container = WorkerContainer()
    use_case = ProcessTopographyUseCase(
        job_repo=container.job_repository(db),
        aoi_repo=container.aoi_geometry_repository(db),
        topo_provider=container.topography_provider(),
        storage=container.object_storage(),
        topo_repo=container.topography_repository(db),
    )

    command = ProcessTopographyCommand(
        job_id=str(job_id),
        tenant_id=payload.get("tenant_id"),
        aoi_id=payload.get("aoi_id"),
    )

    return asyncio.run(use_case.execute(command)).model_dump()
