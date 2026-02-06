"""Use case for ALERTS_WEEK job."""
from __future__ import annotations

import structlog

from worker.application.dtos.alerts_week import AlertsWeekCommand, AlertsWeekResult
from worker.domain.ports.alerts_provider import AlertRepository, AlertsObservationsRepository, TenantSettingsRepository
from worker.domain.ports.job_repository import JobRepository

logger = structlog.get_logger()


class AlertsWeekUseCase:
    def __init__(
        self,
        job_repo: JobRepository,
        settings_repo: TenantSettingsRepository,
        observations_repo: AlertsObservationsRepository,
        alert_repo: AlertRepository,
    ) -> None:
        self._job_repo = job_repo
        self._settings_repo = settings_repo
        self._observations_repo = observations_repo
        self._alert_repo = alert_repo

    def execute(self, command: AlertsWeekCommand) -> AlertsWeekResult:
        logger.info("alerts_week_start", job_id=command.job_id)
        self._job_repo.mark_status(command.job_id, "RUNNING")
        self._job_repo.commit()

        try:
            min_valid_ratio = self._settings_repo.get_min_valid_pixel_ratio(tenant_id=command.tenant_id)

            obs = self._observations_repo.get_observation(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
                year=command.year,
                week=command.week,
            )
            if not obs:
                self._job_repo.mark_status(command.job_id, "DONE")
                self._job_repo.commit()
                return AlertsWeekResult(status="NO_DATA", reason="no_observation")

            alerts_to_create = []

            if obs["status"] == "NO_DATA" or obs["valid_pixel_ratio"] < min_valid_ratio:
                alerts_to_create.append(
                    {
                        "alert_type": "NO_DATA",
                        "severity": "LOW",
                        "confidence": "HIGH",
                        "evidence": {
                            "valid_pixel_ratio": obs["valid_pixel_ratio"],
                            "threshold": min_valid_ratio,
                            "status": obs["status"],
                        },
                    }
                )

            if obs.get("ndvi_mean") is not None and obs["ndvi_mean"] < 0.3:
                severity = "HIGH" if obs["ndvi_mean"] < 0.2 else "MEDIUM"
                alerts_to_create.append(
                    {
                        "alert_type": "LOW_NDVI",
                        "severity": severity,
                        "confidence": "HIGH",
                        "evidence": {
                            "ndvi_mean": obs["ndvi_mean"],
                            "ndvi_p10": obs["ndvi_p10"],
                            "threshold": 0.3,
                        },
                    }
                )

            prev_obs = self._observations_repo.get_previous_observation(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
                year=command.year,
                week=command.week,
            )
            if prev_obs and prev_obs.get("ndvi_mean") is not None and obs.get("ndvi_mean") is not None:
                decline = prev_obs["ndvi_mean"] - obs["ndvi_mean"]
                if decline > 0.15:
                    alerts_to_create.append(
                        {
                            "alert_type": "RAPID_DECLINE",
                            "severity": "HIGH",
                            "confidence": "MEDIUM",
                            "evidence": {
                                "current_ndvi": obs["ndvi_mean"],
                                "previous_ndvi": prev_obs["ndvi_mean"],
                                "decline": decline,
                            },
                        }
                    )

            persistent_count = self._observations_repo.count_persistent_anomalies(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
                year=command.year,
                week=command.week,
            )
            if persistent_count >= 3:
                alerts_to_create.append(
                    {
                        "alert_type": "PERSISTENT_ANOMALY",
                        "severity": "MEDIUM",
                        "confidence": "HIGH",
                        "evidence": {
                            "weeks_count": persistent_count,
                            "current_anomaly": obs.get("anomaly"),
                        },
                    }
                )

            for alert in alerts_to_create:
                existing = self._alert_repo.get_existing(
                    tenant_id=command.tenant_id,
                    aoi_id=command.aoi_id,
                    year=command.year,
                    week=command.week,
                    alert_type=alert["alert_type"],
                )
                if existing:
                    self._alert_repo.update_alert(
                        alert_id=existing["id"],
                        severity=alert["severity"],
                        confidence=alert["confidence"],
                        evidence=alert["evidence"],
                    )
                else:
                    self._alert_repo.create_alert(
                        tenant_id=command.tenant_id,
                        aoi_id=command.aoi_id,
                        year=command.year,
                        week=command.week,
                        alert_type=alert["alert_type"],
                        severity=alert["severity"],
                        confidence=alert["confidence"],
                        evidence=alert["evidence"],
                    )

            self._job_repo.mark_status(command.job_id, "DONE")
            self._job_repo.commit()

            return AlertsWeekResult(
                status="OK",
                alerts_created=len(alerts_to_create),
                alert_types=[a["alert_type"] for a in alerts_to_create] if alerts_to_create else [],
            )
        except Exception as exc:
            logger.error("alerts_week_failed", job_id=command.job_id, error=str(exc), exc_info=True)
            self._job_repo.mark_status(command.job_id, "FAILED", error_message=str(exc))
            self._job_repo.commit()
            raise
