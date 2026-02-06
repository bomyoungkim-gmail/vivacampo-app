"""Use case for PROCESS_WEEK job."""
from __future__ import annotations

from typing import Any, Callable

import structlog

from worker.application.dtos.process_week import ProcessWeekCommand, ProcessWeekResult
from worker.domain.ports.job_repository import JobRepository

logger = structlog.get_logger()

DynamicProcessor = Callable[[str, dict, Any], dict]


class ProcessWeekUseCase:
    def __init__(
        self,
        job_repo: JobRepository,
        dynamic_processor: DynamicProcessor,
    ) -> None:
        self._job_repo = job_repo
        self._dynamic_processor = dynamic_processor

    async def execute(self, command: ProcessWeekCommand, db: Any) -> ProcessWeekResult:
        logger.info(
            "process_week_start",
            job_id=command.job_id,
            use_dynamic_tiling=command.use_dynamic_tiling,
        )
        self._job_repo.mark_status(command.job_id, "RUNNING")
        self._job_repo.commit()

        try:
            if not command.use_dynamic_tiling:
                logger.warning(
                    "process_week_dynamic_tiling_forced",
                    job_id=command.job_id,
                )
            result = self._dynamic_processor(command.job_id, command.payload, db)
            self._job_repo.mark_status(command.job_id, "DONE")
            self._job_repo.commit()
            return ProcessWeekResult(status="DONE", details=result)
        except Exception as exc:
            logger.error("process_week_failed", job_id=command.job_id, error=str(exc), exc_info=True)
            self._job_repo.mark_status(command.job_id, "FAILED", error_message=str(exc))
            self._job_repo.commit()
            raise
