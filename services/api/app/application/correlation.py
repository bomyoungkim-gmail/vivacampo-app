from datetime import datetime, timedelta
from typing import List

from sqlalchemy import text
from sqlalchemy.orm import Session


class CorrelationService:
    def __init__(self, db: Session):
        self.db = db

    def fetch_correlation_data(self, aoi_id: str, tenant_id: str, weeks: int) -> List[dict]:
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks)

        sql = text("""
            WITH weeks AS (
                SELECT da.year, da.week, da.ndvi_mean AS ndvi, da.created_at
                FROM derived_assets da
                WHERE da.aoi_id = :aoi_id
                  AND da.tenant_id = :tenant_id
                  AND da.created_at >= :start_date
            ),
            radar AS (
                SELECT dr.year, dr.week, dr.rvi_mean AS rvi
                FROM derived_radar_assets dr
                WHERE dr.aoi_id = :aoi_id
                  AND dr.tenant_id = :tenant_id
                  AND dr.created_at >= :start_date
            ),
            weather AS (
                SELECT EXTRACT(YEAR FROM dw.date)::int AS year,
                       EXTRACT(WEEK FROM dw.date)::int AS week,
                       SUM(dw.precip_sum) AS rain_mm,
                       AVG((dw.temp_max + dw.temp_min) / 2.0) AS temp_avg
                FROM derived_weather_daily dw
                WHERE dw.aoi_id = :aoi_id
                  AND dw.tenant_id = :tenant_id
                  AND dw.date >= :start_date
                GROUP BY EXTRACT(YEAR FROM dw.date), EXTRACT(WEEK FROM dw.date)
            )
            SELECT w.year, w.week, w.ndvi, r.rvi, wt.rain_mm, wt.temp_avg
            FROM weeks w
            LEFT JOIN radar r ON w.year = r.year AND w.week = r.week
            LEFT JOIN weather wt ON w.year = wt.year AND w.week = wt.week
            ORDER BY w.year, w.week
        """)

        result = self.db.execute(sql, {
            "aoi_id": aoi_id,
            "tenant_id": tenant_id,
            "start_date": start_date,
        })

        return [
            {
                "date": f"{row.year}-W{row.week:02d}",
                "ndvi": row.ndvi,
                "rvi": row.rvi,
                "rain_mm": float(row.rain_mm) if row.rain_mm is not None else None,
                "temp_avg": float(row.temp_avg) if row.temp_avg is not None else None,
            }
            for row in result
        ]

    def generate_insights(self, data: List[dict]) -> List[dict]:
        insights = []
        if len(data) < 2:
            return insights

        for i in range(1, len(data)):
            current, previous = data[i], data[i - 1]

            # Rain effect
            if previous.get("rain_mm") and previous["rain_mm"] > 10:
                if current.get("ndvi") is not None and previous.get("ndvi") is not None:
                    ndvi_change = current["ndvi"] - previous["ndvi"]
                    if ndvi_change > 0.05:
                        insights.append({
                            "type": "rain_effect",
                            "message": (
                                f"Chuva de {previous['rain_mm']:.1f}mm em {previous['date']} "
                                f"→ NDVI subiu {ndvi_change * 100:.0f}%"
                            ),
                            "severity": "info",
                        })

            # Radar fallback
            if current.get("ndvi") is None and current.get("rvi") is not None:
                insights.append({
                    "type": "radar_fallback",
                    "message": (
                        f"Dia nublado em {current['date']}. "
                        f"Usando radar (RVI: {current['rvi']:.2f})"
                    ),
                    "severity": "info",
                })

            # Vigor drop
            if current.get("ndvi") is not None and previous.get("ndvi") is not None:
                ndvi_drop = previous["ndvi"] - current["ndvi"]
                if ndvi_drop > 0.1:
                    insights.append({
                        "type": "vigor_drop",
                        "message": (
                            f"Queda de vigor de {ndvi_drop * 100:.0f}% "
                            f"entre {previous['date']} e {current['date']}"
                        ),
                        "severity": "warning",
                    })

        return insights

    def fetch_year_over_year(self, aoi_id: str, tenant_id: str) -> dict:
        latest_year_sql = text("""
            SELECT MAX(year) AS year
            FROM derived_assets
            WHERE aoi_id = :aoi_id AND tenant_id = :tenant_id
        """)
        latest = self.db.execute(latest_year_sql, {"aoi_id": aoi_id, "tenant_id": tenant_id}).first()
        if not latest or latest.year is None:
            return {}

        current_year = int(latest.year)
        previous_year = current_year - 1

        series_sql = text("""
            SELECT week, ndvi_mean
            FROM derived_assets
            WHERE aoi_id = :aoi_id AND tenant_id = :tenant_id AND year = :year
            ORDER BY week
        """)

        current_rows = self.db.execute(series_sql, {
            "aoi_id": aoi_id,
            "tenant_id": tenant_id,
            "year": current_year,
        })
        previous_rows = self.db.execute(series_sql, {
            "aoi_id": aoi_id,
            "tenant_id": tenant_id,
            "year": previous_year,
        })

        current_series = [{"week": row.week, "ndvi": row.ndvi_mean} for row in current_rows]
        previous_series = [{"week": row.week, "ndvi": row.ndvi_mean} for row in previous_rows]

        return {
            "current_year": current_year,
            "previous_year": previous_year,
            "current_series": current_series,
            "previous_series": previous_series,
        }
