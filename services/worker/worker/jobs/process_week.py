"""
PROCESS_WEEK job handler.

Delegates to CALCULATE_STATS (dynamic tiling).
"""
from __future__ import annotations

import asyncio

import structlog
from sqlalchemy.orm import Session

from worker.application.dtos.process_week import ProcessWeekCommand
from worker.application.use_cases.process_week import ProcessWeekUseCase
from worker.config import settings
from worker.infrastructure.di_container import WorkerContainer

logger = structlog.get_logger()


def process_week_handler(job_id: str, payload: dict, db: Session):
    command = ProcessWeekCommand(
        job_id=str(job_id),
        tenant_id=payload.get("tenant_id"),
        aoi_id=payload.get("aoi_id"),
        year=payload.get("year"),
        week=payload.get("week"),
        payload=payload,
        use_dynamic_tiling=settings.use_dynamic_tiling,
    )

    container = WorkerContainer()
    use_case = ProcessWeekUseCase(
        job_repo=container.job_repository(db),
        dynamic_processor=_dynamic_processor,
    )

    return asyncio.run(use_case.execute(command, db)).model_dump()


def _dynamic_processor(job_id: str, payload: dict, db: Session) -> dict:
    from worker.jobs.calculate_stats import calculate_stats_handler

    logger.info(
        "process_week_dynamic_tiling_mode",
        job_id=job_id,
        message="Delegating to CALCULATE_STATS (no COG generation)",
    )
    return calculate_stats_handler(job_id, payload, db)
