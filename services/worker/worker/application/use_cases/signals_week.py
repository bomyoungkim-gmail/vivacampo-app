"""Use case for SIGNALS_WEEK job."""
from __future__ import annotations

import structlog

from worker.application.dtos.signals_week import SignalsWeekCommand, SignalsWeekResult
from worker.config import settings
from worker.domain.ports.job_repository import JobRepository
from worker.domain.ports.signals_provider import (
    AoiInfoRepository,
    SignalRepository,
    SignalsObservationsRepository,
)
from worker.shared.utils import get_week_date_range
from worker.signals.features import (
    extract_features,
    calculate_rule_score,
    calculate_ml_score,
    calculate_final_score,
    determine_severity,
    determine_confidence,
)
from worker.signals.change_detection import (
    detect_change_bfast_like,
    detect_change_simple,
    calculate_change_score,
)
from worker.signals.signal_types import (
    determine_signal_type,
    get_recommended_actions,
)

logger = structlog.get_logger()


class SignalsWeekUseCase:
    def __init__(
        self,
        job_repo: JobRepository,
        observations_repo: SignalsObservationsRepository,
        aoi_repo: AoiInfoRepository,
        signal_repo: SignalRepository,
    ) -> None:
        self._job_repo = job_repo
        self._observations_repo = observations_repo
        self._aoi_repo = aoi_repo
        self._signal_repo = signal_repo

    def execute(self, command: SignalsWeekCommand) -> SignalsWeekResult:
        logger.info("signals_week_start", job_id=command.job_id)
        self._job_repo.mark_status(command.job_id, "RUNNING")
        self._job_repo.commit()

        try:
            observations = self._observations_repo.list_recent(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
                limit=settings.signals_min_history_weeks + 10,
            )

            if len(observations) < settings.signals_min_history_weeks:
                self._job_repo.mark_status(command.job_id, "DONE")
                self._job_repo.commit()
                return SignalsWeekResult(status="NO_DATA", reason="insufficient_history")

            use_type = self._aoi_repo.get_use_type(tenant_id=command.tenant_id, aoi_id=command.aoi_id)
            features = extract_features(observations)
            if not features:
                self._job_repo.mark_status(command.job_id, "DONE")
                self._job_repo.commit()
                return SignalsWeekResult(status="NO_DATA", reason="no_features")

            if settings.signals_change_detection == "BFastLike":
                change_detection = detect_change_bfast_like(
                    observations,
                    persistence_weeks=settings.signals_persistence_weeks,
                )
            else:
                change_detection = detect_change_simple(observations)

            rule_score = calculate_rule_score(features, use_type)
            change_score = calculate_change_score(change_detection)
            ml_score = calculate_ml_score(features)
            final_score = calculate_final_score(rule_score, change_score, ml_score)

            if final_score < settings.signals_score_threshold:
                self._job_repo.mark_status(command.job_id, "DONE")
                self._job_repo.commit()
                return SignalsWeekResult(status="NO_DATA", reason="below_threshold")

            signal_type = determine_signal_type(use_type, features, change_detection or {})
            recommended_actions = get_recommended_actions(signal_type)

            avg_valid_pixel_ratio = sum(o.get("valid_pixel_ratio", 0) for o in observations) / len(observations)
            severity = determine_severity(final_score)
            confidence = determine_confidence(final_score, avg_valid_pixel_ratio, len(observations))

            evidence = {
                "window_weeks": len(observations),
                "baseline_ref": observations[0].get("baseline", 0),
                "valid_pixel_ratio_summary": {
                    "mean": avg_valid_pixel_ratio,
                    "min": min(o.get("valid_pixel_ratio", 0) for o in observations),
                },
                "change_detection": change_detection or {},
            }

            existing = self._signal_repo.get_existing(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
                year=command.year,
                week=command.week,
                signal_type=signal_type,
                pipeline_version=settings.pipeline_version,
            )

            if existing:
                self._signal_repo.update_signal(
                    signal_id=existing["id"],
                    score=final_score,
                    evidence=evidence,
                    features=features,
                )
            else:
                _, end_date = get_week_date_range(command.year, command.week)
                self._signal_repo.create_signal(
                    tenant_id=command.tenant_id,
                    aoi_id=command.aoi_id,
                    year=command.year,
                    week=command.week,
                    signal_type=signal_type,
                    severity=severity,
                    confidence=confidence,
                    score=final_score,
                    evidence=evidence,
                    features=features,
                    recommended_actions=recommended_actions,
                    created_at=end_date,
                    pipeline_version=settings.pipeline_version,
                    model_version=settings.signals_model_version,
                    change_method=settings.signals_change_detection,
                )

            self._job_repo.mark_status(command.job_id, "DONE")
            self._job_repo.commit()
            return SignalsWeekResult(status="OK", signal_type=signal_type, score=final_score)
        except Exception as exc:
            logger.error("signals_week_failed", job_id=command.job_id, error=str(exc), exc_info=True)
            self._job_repo.mark_status(command.job_id, "FAILED", error_message=str(exc))
            self._job_repo.commit()
            raise
