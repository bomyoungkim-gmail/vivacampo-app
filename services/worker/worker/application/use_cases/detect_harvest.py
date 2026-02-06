"""Use case for DETECT_HARVEST job."""
from __future__ import annotations

from datetime import date

import structlog

from worker.application.dtos.detect_harvest import DetectHarvestCommand, DetectHarvestResult
from worker.domain.ports.harvest_provider import HarvestSignalRepository, RadarMetricsRepository
from worker.domain.ports.job_repository import JobRepository

logger = structlog.get_logger()


class DetectHarvestUseCase:
    def __init__(
        self,
        job_repo: JobRepository,
        radar_repo: RadarMetricsRepository,
        signal_repo: HarvestSignalRepository,
    ) -> None:
        self._job_repo = job_repo
        self._radar_repo = radar_repo
        self._signal_repo = signal_repo

    def execute(self, command: DetectHarvestCommand) -> DetectHarvestResult:
        logger.info("detect_harvest_start", job_id=command.job_id)
        self._job_repo.mark_status(command.job_id, "RUNNING")
        self._job_repo.commit()

        try:
            current_rvi = self._radar_repo.get_rvi_mean(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
                year=command.year,
                week=command.week,
            )

            prev_year, prev_week = _previous_week(command.year, command.week)
            previous_rvi = self._radar_repo.get_rvi_mean(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
                year=prev_year,
                week=prev_week,
            )

            if current_rvi is None or previous_rvi is None:
                self._job_repo.mark_status(command.job_id, "DONE")
                self._job_repo.commit()
                return DetectHarvestResult(status="NO_DATA", detected=False, reason="missing_rvi")

            rvi_drop = previous_rvi - current_rvi
            harvest_threshold = 0.3

            if rvi_drop > harvest_threshold:
                self._signal_repo.create_signal(
                    tenant_id=command.tenant_id,
                    aoi_id=command.aoi_id,
                    year=command.year,
                    week=command.week,
                    rvi_current=current_rvi,
                    rvi_previous=previous_rvi,
                )
                detected = True
            else:
                detected = False

            self._job_repo.mark_status(command.job_id, "DONE")
            self._job_repo.commit()
            return DetectHarvestResult(status="OK", detected=detected)
        except Exception as exc:
            logger.error("detect_harvest_failed", job_id=command.job_id, error=str(exc), exc_info=True)
            self._job_repo.mark_status(command.job_id, "FAILED", error_message=str(exc))
            self._job_repo.commit()
            raise


def _previous_week(year: int, week: int) -> tuple[int, int]:
    if week == 1:
        last_day_prev_year = date(year - 1, 12, 28)
        prev_year, prev_week, _ = last_day_prev_year.isocalendar()
        return prev_year, prev_week
    return year, week - 1
