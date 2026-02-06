"""Use case for backfill job orchestration."""
from __future__ import annotations

from datetime import date, timedelta
import hashlib
from typing import Dict, Iterable, Tuple

import structlog

from worker.application.dtos.backfill import BackfillCommand, BackfillResult
from worker.domain.ports.job_repository import JobQueue, JobRepository, SeasonRepository

logger = structlog.get_logger()


class BackfillUseCase:
    def __init__(
        self,
        job_repo: JobRepository,
        season_repo: SeasonRepository,
        queue: JobQueue,
    ) -> None:
        self._job_repo = job_repo
        self._season_repo = season_repo
        self._queue = queue

    async def execute(self, command: BackfillCommand) -> BackfillResult:
        logger.info("backfill_started", job_id=command.job_id)
        self._job_repo.mark_status(command.job_id, "RUNNING")
        self._job_repo.commit()

        weeks_to_process = list(_weeks_in_range(command.from_date, command.to_date))
        logger.info(
            "backfill_weeks_calculated",
            total_weeks=len(weeks_to_process),
            from_date=str(command.from_date),
            to_date=str(command.to_date),
        )

        jobs_created: Dict[str, int] = {
            "PROCESS_WEEK": 0,
            "PROCESS_RADAR_WEEK": 0,
            "PROCESS_WEATHER": 0,
            "PROCESS_TOPOGRAPHY": 0,
            "ALERTS_WEEK": 0,
            "SIGNALS_WEEK": 0,
            "FORECAST_WEEK": 0,
        }

        self._create_weather_job(command, jobs_created)
        self._create_topography_job(command, jobs_created)

        for year, week in weeks_to_process:
            self._create_week_jobs(command, year, week, jobs_created)

        self._job_repo.commit()
        self._job_repo.mark_status(command.job_id, "DONE")
        self._job_repo.commit()

        total_jobs = sum(jobs_created.values())
        logger.info(
            "backfill_completed",
            job_id=command.job_id,
            weeks_processed=len(weeks_to_process),
            jobs_created=jobs_created,
        )

        return BackfillResult(
            weeks_processed=len(weeks_to_process),
            jobs_created=jobs_created,
            total_jobs=total_jobs,
        )

    def _create_weather_job(self, command: BackfillCommand, jobs_created: Dict[str, int]) -> None:
        job_key = _hash_key(
            command.tenant_id,
            command.aoi_id,
            command.from_date.isoformat(),
            command.to_date.isoformat(),
            "PROCESS_WEATHER",
            command.pipeline_version,
        )
        payload = {
            "tenant_id": command.tenant_id,
            "aoi_id": command.aoi_id,
            "start_date": command.from_date.isoformat(),
            "end_date": command.to_date.isoformat(),
        }
        self._upsert_and_enqueue(
            job_key=job_key,
            job_type="PROCESS_WEATHER",
            payload=payload,
            jobs_created=jobs_created,
        )

    def _create_topography_job(self, command: BackfillCommand, jobs_created: Dict[str, int]) -> None:
        job_key = _hash_key(
            command.tenant_id,
            command.aoi_id,
            "PROCESS_TOPOGRAPHY",
            command.pipeline_version,
        )
        payload = {
            "tenant_id": command.tenant_id,
            "aoi_id": command.aoi_id,
        }
        self._upsert_and_enqueue(
            job_key=job_key,
            job_type="PROCESS_TOPOGRAPHY",
            payload=payload,
            jobs_created=jobs_created,
        )

    def _create_week_jobs(
        self,
        command: BackfillCommand,
        year: int,
        week: int,
        jobs_created: Dict[str, int],
    ) -> None:
        payload = {
            "tenant_id": command.tenant_id,
            "aoi_id": command.aoi_id,
            "year": year,
            "week": week,
        }
        self._upsert_and_enqueue(
            job_key=_hash_key(
                command.tenant_id,
                command.aoi_id,
                str(year),
                str(week),
                "PROCESS_WEEK",
                command.pipeline_version,
            ),
            job_type="PROCESS_WEEK",
            payload=payload,
            jobs_created=jobs_created,
        )
        self._upsert_and_enqueue(
            job_key=_hash_key(
                command.tenant_id,
                command.aoi_id,
                str(year),
                str(week),
                "PROCESS_RADAR_WEEK",
                command.pipeline_version,
            ),
            job_type="PROCESS_RADAR_WEEK",
            payload=payload,
            jobs_created=jobs_created,
        )
        self._upsert_and_enqueue(
            job_key=_hash_key(
                command.tenant_id,
                command.aoi_id,
                str(year),
                str(week),
                "ALERTS_WEEK",
                command.pipeline_version,
            ),
            job_type="ALERTS_WEEK",
            payload=payload,
            jobs_created=jobs_created,
        )

        if command.signals_enabled:
            self._upsert_and_enqueue(
                job_key=_hash_key(
                    command.tenant_id,
                    command.aoi_id,
                    str(year),
                    str(week),
                    "SIGNALS_WEEK",
                    command.pipeline_version,
                ),
                job_type="SIGNALS_WEEK",
                payload=payload,
                jobs_created=jobs_created,
            )

        if self._season_repo.has_season(command.tenant_id, command.aoi_id):
            self._upsert_and_enqueue(
                job_key=_hash_key(
                    command.tenant_id,
                    command.aoi_id,
                    str(year),
                    str(week),
                    "FORECAST_WEEK",
                    command.pipeline_version,
                ),
                job_type="FORECAST_WEEK",
                payload=payload,
                jobs_created=jobs_created,
            )

    def _upsert_and_enqueue(
        self,
        *,
        job_key: str,
        job_type: str,
        payload: dict,
        jobs_created: Dict[str, int],
    ) -> None:
        job_id = self._job_repo.upsert_job(
            tenant_id=payload["tenant_id"],
            aoi_id=payload["aoi_id"],
            job_type=job_type,
            job_key=job_key,
            payload=payload,
        )
        if job_id:
            jobs_created[job_type] += 1
            self._queue.enqueue(job_id=job_id, job_type=job_type, payload=payload)


def _hash_key(*parts: str) -> str:
    value = "".join(parts)
    return hashlib.sha256(value.encode()).hexdigest()


def _weeks_in_range(start: date, end: date) -> Iterable[Tuple[int, int]]:
    current = start
    while current <= end:
        iso_year, iso_week, _ = current.isocalendar()
        yield iso_year, iso_week
        current += timedelta(days=7)
