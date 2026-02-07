"""Nitrogen use case using repository port."""
from __future__ import annotations

from typing import Optional

from app.application.decorators import require_tenant
from app.application.dtos.nitrogen import GetNitrogenStatusCommand, NitrogenStatusResult
from app.domain.ports.nitrogen_repository import INitrogenRepository


class GetNitrogenStatusUseCase:
    def __init__(self, repo: INitrogenRepository):
        self.repo = repo

    @require_tenant
    def execute(self, command: GetNitrogenStatusCommand) -> NitrogenStatusResult | None:
        indices = self.repo.get_latest_indices(command.tenant_id, command.aoi_id)
        if not indices:
            return None

        ndvi = indices.get("ndvi_mean")
        ndre = indices.get("ndre_mean")
        reci = indices.get("reci_mean")

        status_str, confidence, recommendation = self._detect_nitrogen_status(ndvi, ndre, reci)

        zone_map_url = None
        if status_str == "DEFICIENT":
            zone_map_url = f"{command.base_url}/v1/tiles/aois/{command.aoi_id}/{{z}}/{{x}}/{{y}}.png?index=srre"

        return NitrogenStatusResult(
            status=status_str,
            confidence=confidence,
            ndvi_mean=ndvi,
            ndre_mean=ndre,
            reci_mean=reci,
            recommendation=recommendation,
            zone_map_url=zone_map_url,
        )

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
