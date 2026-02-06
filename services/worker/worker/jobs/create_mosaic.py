"""
CREATE_MOSAIC Job

Creates MosaicJSON files for a specific week/collection.
MosaicJSONs are virtual aggregations of Sentinel scenes that allow
TiTiler to serve tiles dynamically without storing COGs per-AOI.

This job runs once per week (globally, not per-AOI) and creates
a MosaicJSON that references all available Sentinel-2 scenes for Brazil.
"""
from __future__ import annotations

import structlog
from sqlalchemy.orm import Session

from worker.application.dtos.create_mosaic import CreateMosaicCommand
from worker.application.use_cases.create_mosaic import CreateMosaicUseCase, iso_week_to_dates
from worker.config import settings
from worker.infrastructure.di_container import WorkerContainer

logger = structlog.get_logger()

def create_mosaic_handler(job_id: str, payload: dict, db: Session) -> dict:
    year = payload.get("year")
    week = payload.get("week")
    collection = payload.get("collection", "sentinel-2-l2a")
    max_cloud_cover = payload.get("max_cloud_cover", 30)

    if not year or not week:
        raise ValueError("year and week are required in payload")

    container = WorkerContainer()
    use_case = CreateMosaicUseCase(
        job_repo=container.job_repository(db),
        provider=container.mosaic_provider(),
        storage=container.mosaic_storage(),
        registry=container.mosaic_registry(db),
    )

    command = CreateMosaicCommand(
        job_id=str(job_id),
        year=year,
        week=week,
        collection=collection,
        max_cloud_cover=max_cloud_cover,
    )

    return use_case.execute(command).model_dump()


def ensure_mosaic_exists(year: int, week: int, collection: str = "sentinel-2-l2a") -> str:
    """
    Check if mosaic exists in S3, return URL if it does.
    Used by other jobs to ensure mosaic is available before calculating stats.
    """
    container = WorkerContainer()
    key = f"mosaics/{collection}/{year}/w{week:02d}.json"
    if container.mosaic_storage().exists(key=key):
        return f"s3://{settings.s3_bucket}/{key}"
    return None
