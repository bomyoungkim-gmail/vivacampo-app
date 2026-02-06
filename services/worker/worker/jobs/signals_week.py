"""SIGNALS_WEEK job handler."""
from __future__ import annotations

import structlog
from sqlalchemy.orm import Session

from worker.application.dtos.signals_week import SignalsWeekCommand
from worker.application.use_cases.signals_week import SignalsWeekUseCase
from worker.infrastructure.di_container import WorkerContainer

logger = structlog.get_logger()


def signals_week_handler(job_id: str, payload: dict, db: Session):
    logger.info("signals_week_start", job_id=job_id, payload=payload)

    container = WorkerContainer()
    use_case = SignalsWeekUseCase(
        job_repo=container.job_repository(db),
        observations_repo=container.signals_observations_repository(db),
        aoi_repo=container.aoi_info_repository(db),
        signal_repo=container.signal_repository(db),
    )

    command = SignalsWeekCommand(
        job_id=str(job_id),
        tenant_id=payload.get("tenant_id"),
        aoi_id=payload.get("aoi_id"),
        year=payload.get("year"),
        week=payload.get("week"),
    )

    return use_case.execute(command).model_dump()
