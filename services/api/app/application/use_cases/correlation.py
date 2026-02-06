"""Correlation use cases using repository ports."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from app.application.dtos.correlation import (
    CorrelationCommand,
    CorrelationDataPoint,
    CorrelationResult,
    Insight,
    YearOverYearCommand,
    YearOverYearPoint,
    YearOverYearResult,
)
from app.domain.ports.correlation_repository import ICorrelationRepository


class CorrelationUseCase:
    def __init__(self, repo: ICorrelationRepository):
        self.repo = repo

    def execute(self, command: CorrelationCommand) -> CorrelationResult:
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=command.weeks)
        data = self.repo.fetch_correlation_data(command.aoi_id, command.tenant_id, start_date)
        insights = self._generate_insights(data)
        return CorrelationResult(
            data=[CorrelationDataPoint(**d) for d in data],
            insights=[Insight(**i) for i in insights],
        )

    def _generate_insights(self, data: List[dict]) -> List[dict]:
        insights = []
        if len(data) < 2:
            return insights

        for i in range(1, len(data)):
            current, previous = data[i], data[i - 1]

            if previous.get("rain_mm") and previous["rain_mm"] > 10:
                if current.get("ndvi") is not None and previous.get("ndvi") is not None:
                    ndvi_change = current["ndvi"] - previous["ndvi"]
                    if ndvi_change > 0.05:
                        insights.append(
                            {
                                "type": "rain_effect",
                                "message": (
                                    f"Chuva de {previous['rain_mm']:.1f}mm em {previous['date']} "
                                    f"→ NDVI subiu {ndvi_change * 100:.0f}%"
                                ),
                                "severity": "info",
                            }
                        )

            if current.get("ndvi") is None and current.get("rvi") is not None:
                insights.append(
                    {
                        "type": "radar_fallback",
                        "message": (
                            f"Dia nublado em {current['date']}. "
                            f"Usando radar (RVI: {current['rvi']:.2f})"
                        ),
                        "severity": "info",
                    }
                )

            if current.get("ndvi") is not None and previous.get("ndvi") is not None:
                ndvi_drop = previous["ndvi"] - current["ndvi"]
                if ndvi_drop > 0.1:
                    insights.append(
                        {
                            "type": "vigor_drop",
                            "message": (
                                f"Queda de vigor de {ndvi_drop * 100:.0f}% "
                                f"entre {previous['date']} e {current['date']}"
                            ),
                            "severity": "warning",
                        }
                    )

        return insights


class YearOverYearUseCase:
    def __init__(self, repo: ICorrelationRepository):
        self.repo = repo

    def execute(self, command: YearOverYearCommand) -> YearOverYearResult | None:
        result = self.repo.fetch_year_over_year(command.aoi_id, command.tenant_id)
        if not result:
            return None
        return YearOverYearResult(
            current_year=result["current_year"],
            previous_year=result["previous_year"],
            current_series=[YearOverYearPoint(**d) for d in result["current_series"]],
            previous_series=[YearOverYearPoint(**d) for d in result["previous_series"]],
        )
