"""
ALERTS_WEEK handler - Generate risk alerts based on observations.
Detects conditions that require immediate attention.
"""
from __future__ import annotations

import structlog
from sqlalchemy.orm import Session

from worker.application.dtos.alerts_week import AlertsWeekCommand
from worker.application.use_cases.alerts_week import AlertsWeekUseCase
from worker.infrastructure.di_container import WorkerContainer

logger = structlog.get_logger()


def handle_alerts_week(job: dict, db: Session):
    logger.info("alerts_week_started", job_id=job["id"])

    payload = job.get("payload", {})
    command = AlertsWeekCommand(
        job_id=str(job["id"]),
        tenant_id=job.get("tenant_id"),
        aoi_id=job.get("aoi_id"),
        year=payload.get("year"),
        week=payload.get("week"),
    )

    container = WorkerContainer()
    use_case = AlertsWeekUseCase(
        job_repo=container.job_repository(db),
        settings_repo=container.tenant_settings_repository(db),
        observations_repo=container.alerts_observations_repository(db),
        alert_repo=container.alert_repository(db),
    )

    return use_case.execute(command).model_dump()
