"""
WARM_CACHE Job

Pre-warms CDN cache for AOI tiles after backfill completes.
This ensures users experience fast tile loading on first access.
"""
from __future__ import annotations

import asyncio
import structlog
from sqlalchemy.orm import Session

from worker.application.dtos.warm_cache import WarmCacheCommand
from worker.application.use_cases.warm_cache import WarmCacheUseCase
from worker.infrastructure.di_container import WorkerContainer

logger = structlog.get_logger()


def warm_cache_handler(job: dict, db: Session) -> dict:
    payload = job.get("payload", {})
    command = WarmCacheCommand(
        job_id=str(job["id"]),
        tenant_id=payload.get("tenant_id"),
        aoi_id=payload.get("aoi_id"),
        indices=payload.get("indices"),
        zoom_levels=payload.get("zoom_levels"),
    )

    container = WorkerContainer()
    use_case = WarmCacheUseCase(
        job_repo=container.job_repository(db),
        bounds_repo=container.aoi_bounds_repository(db),
        tile_client=container.tile_warm_client(),
    )

    return asyncio.run(use_case.execute(command)).model_dump()


def warm_cache_sync_handler(job_id: str, payload: dict, db: Session) -> dict:
    job = {"id": job_id, "payload": payload}
    return warm_cache_handler(job, db)
