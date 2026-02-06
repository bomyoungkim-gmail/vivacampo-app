from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session


class GetNitrogenStatusUseCase:
    def __init__(self, db: Session):
        self.db = db

    def execute(self, tenant_id: str, aoi_id: str, base_url: str) -> dict:
        indices = self._get_latest_indices(tenant_id, aoi_id)
        if not indices:
            return {}

        ndvi = indices.get("ndvi_mean")
        ndre = indices.get("ndre_mean")
        reci = indices.get("reci_mean")

        status_str, confidence, recommendation = self._detect_nitrogen_status(ndvi, ndre, reci)

        zone_map_url = None
        if status_str == "DEFICIENT":
            zone_map_url = f"{base_url}/v1/tiles/aois/{aoi_id}/{{z}}/{{x}}/{{y}}.png?index=srre"

        return {
            "status": status_str,
            "confidence": confidence,
            "ndvi_mean": ndvi,
            "ndre_mean": ndre,
            "reci_mean": reci,
            "recommendation": recommendation,
            "zone_map_url": zone_map_url,
        }

    def _get_latest_indices(self, tenant_id: str, aoi_id: str) -> dict:
        sql = text("""
            SELECT ndvi_mean, ndre_mean, reci_mean, year, week
            FROM derived_assets
            WHERE aoi_id = :aoi_id AND tenant_id = :tenant_id
            ORDER BY year DESC, week DESC
            LIMIT 1
        """)
        result = self.db.execute(sql, {"aoi_id": aoi_id, "tenant_id": tenant_id}).first()
        if result:
            return {
                "ndvi_mean": result.ndvi_mean,
                "ndre_mean": result.ndre_mean,
                "reci_mean": result.reci_mean,
            }
        return {}

    def _detect_nitrogen_status(
        self,
        ndvi: Optional[float],
        ndre: Optional[float],
        reci: Optional[float],
    ) -> tuple[str, float, str]:
        if ndvi is None or ndre is None or reci is None:
            return "UNKNOWN", 0.0, "Dados insuficientes para análise"

        is_high_ndvi = ndvi > 0.7
        is_low_ndre = ndre < 0.5
        is_low_reci = reci < 1.5
        conditions_met = sum([is_high_ndvi, is_low_ndre, is_low_reci])

        if conditions_met >= 3:
            return (
                "DEFICIENT",
                0.9,
                "Deficiência de nitrogênio detectada. Recomenda-se aplicação em taxa variável.",
            )
        if conditions_met >= 2:
            return (
                "DEFICIENT",
                0.7,
                "Possível deficiência de nitrogênio. Monitorar nas próximas semanas.",
            )
        if ndvi > 0.6 and ndre > 0.4:
            return "ADEQUATE", 0.85, "Níveis de nitrogênio adequados."
        return "UNKNOWN", 0.5, "Condições mistas. Recomenda-se análise de solo."
