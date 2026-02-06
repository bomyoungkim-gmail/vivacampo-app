"""
Harvest detection via VH backscatter proxy (RVI drop).
Scientific basis: VH drops > 3dB when crops are harvested.
"""
from __future__ import annotations

import structlog
from sqlalchemy.orm import Session

from worker.application.dtos.detect_harvest import DetectHarvestCommand
from worker.application.use_cases.detect_harvest import DetectHarvestUseCase
from worker.infrastructure.di_container import WorkerContainer

logger = structlog.get_logger()


def detect_harvest_handler(job_id: str, payload: dict, db: Session):
    logger.info("detect_harvest_start", job_id=job_id, payload=payload)

    command = DetectHarvestCommand(
        job_id=str(job_id),
        tenant_id=payload.get("tenant_id"),
        aoi_id=payload.get("aoi_id"),
        year=payload.get("year"),
        week=payload.get("week"),
    )

    container = WorkerContainer()
    use_case = DetectHarvestUseCase(
        job_repo=container.job_repository(db),
        radar_repo=container.radar_metrics_repository(db),
        signal_repo=container.harvest_signal_repository(db),
    )

    return use_case.execute(command).model_dump()
