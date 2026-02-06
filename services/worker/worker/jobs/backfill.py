"""
BACKFILL handler - Orchestrate processing of historical data.
Creates PROCESS_WEEK, ALERTS_WEEK, SIGNALS_WEEK, and FORECAST_WEEK jobs for each week.
"""
from __future__ import annotations

from typing import Any, Dict

import structlog
from sqlalchemy.orm import Session

from worker.application.dtos.backfill import BackfillCommand
from worker.application.use_cases.backfill import BackfillUseCase
from worker.config import settings
from worker.infrastructure.di_container import WorkerContainer

logger = structlog.get_logger()


async def handle_backfill(job: Dict[str, Any], db: Session):
    """
    Orchestrate backfill processing for a date range.

    Creates jobs in sequence:
    1. PROCESS_WEEK (generate observations)
    2. ALERTS_WEEK (generate alerts)
    3. SIGNALS_WEEK (generate signals)
    4. FORECAST_WEEK (generate forecasts)
    """
    container = WorkerContainer()
    use_case = BackfillUseCase(
        job_repo=container.job_repository(db),
        season_repo=container.season_repository(db),
        queue=container.job_queue(),
    )

    payload = job.get("payload", {})
    command = BackfillCommand(
        job_id=str(job["id"]),
        tenant_id=str(job["tenant_id"]),
        aoi_id=str(job["aoi_id"]),
        from_date=payload.get("from_date"),
        to_date=payload.get("to_date"),
        pipeline_version=settings.pipeline_version,
        signals_enabled=settings.signals_enabled,
    )

    result = await use_case.execute(command)
    return result.model_dump()
