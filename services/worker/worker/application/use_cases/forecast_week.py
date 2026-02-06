"""Use case for FORECAST_WEEK job."""
from __future__ import annotations

import structlog

from worker.application.dtos.forecast_week import ForecastWeekCommand, ForecastWeekResult
from worker.domain.ports.forecast_provider import (
    ForecastObservationsRepository,
    SeasonRepository,
    YieldForecastRepository,
)
from worker.domain.ports.job_repository import JobRepository

logger = structlog.get_logger()


class ForecastWeekUseCase:
    def __init__(
        self,
        job_repo: JobRepository,
        season_repo: SeasonRepository,
        observations_repo: ForecastObservationsRepository,
        forecast_repo: YieldForecastRepository,
    ) -> None:
        self._job_repo = job_repo
        self._season_repo = season_repo
        self._observations_repo = observations_repo
        self._forecast_repo = forecast_repo

    def execute(self, command: ForecastWeekCommand) -> ForecastWeekResult:
        logger.info("forecast_week_start", job_id=command.job_id)
        self._job_repo.mark_status(command.job_id, "RUNNING")
        self._job_repo.commit()

        try:
            season = self._season_repo.get_active_season(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
            )
            if not season:
                self._job_repo.mark_status(command.job_id, "DONE")
                self._job_repo.commit()
                return ForecastWeekResult(status="NO_DATA", reason="no_active_season")

            observations = self._observations_repo.list_observations(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
            )
            if len(observations) < 4:
                self._job_repo.mark_status(command.job_id, "DONE")
                self._job_repo.commit()
                return ForecastWeekResult(status="NO_DATA", reason="insufficient_history")

            current_season_ndvi = [
                obs["ndvi_mean"]
                for obs in observations
                if obs["year"] == command.year and obs["week"] <= command.week and obs.get("ndvi_mean") is not None
            ]
            if not current_season_ndvi:
                self._job_repo.mark_status(command.job_id, "DONE")
                self._job_repo.commit()
                return ForecastWeekResult(status="NO_DATA", reason="no_current_season_data")

            ndvi_index = sum(current_season_ndvi) / len(current_season_ndvi)

            historical_yields = self._forecast_repo.list_historical_yields(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
                limit=3,
            )

            if historical_yields:
                avg_historical = sum(historical_yields) / len(historical_yields)
                yield_factor = ndvi_index / 0.6
                estimated_yield = avg_historical * yield_factor
            else:
                crop_defaults = {
                    "CORN": 8000,
                    "SOYBEAN": 3500,
                    "WHEAT": 4000,
                    "RICE": 6000,
                }
                base_yield = crop_defaults.get(season.get("crop_type"), 5000)
                yield_factor = ndvi_index / 0.6
                estimated_yield = base_yield * yield_factor

            weeks_to_harvest = 12
            progress = len(current_season_ndvi) / weeks_to_harvest
            if progress < 0.3:
                confidence = "LOW"
            elif progress < 0.7:
                confidence = "MEDIUM"
            else:
                confidence = "HIGH"

            evidence = {
                "ndvi_index": ndvi_index,
                "observations_count": len(current_season_ndvi),
                "yield_factor": yield_factor,
                "historical_yields_count": len(historical_yields) if historical_yields else 0,
            }

            self._forecast_repo.save_forecast(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
                season_id=str(season["id"]),
                year=command.year,
                week=command.week,
                estimated_yield=round(estimated_yield, 2),
                confidence=confidence,
                evidence=evidence,
                method="INDEX_RELATIVE",
                model_version="forecast-v1",
            )

            self._job_repo.mark_status(command.job_id, "DONE")
            self._job_repo.commit()

            return ForecastWeekResult(
                status="OK",
                estimated_yield_kg_ha=round(estimated_yield, 2),
                confidence=confidence,
                ndvi_index=round(ndvi_index, 3),
                observations_count=len(current_season_ndvi),
            )
        except Exception as exc:
            logger.error("forecast_week_failed", job_id=command.job_id, error=str(exc), exc_info=True)
            self._job_repo.mark_status(command.job_id, "FAILED", error_message=str(exc))
            self._job_repo.commit()
            raise
