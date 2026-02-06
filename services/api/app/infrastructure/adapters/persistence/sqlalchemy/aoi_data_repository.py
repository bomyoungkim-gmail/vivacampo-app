"""SQLAlchemy adapter for AOI data (assets/history)."""
from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.ports.aoi_data_repository import IAoiDataRepository
from app.domain.value_objects.tenant_id import TenantId


class SQLAlchemyAoiDataRepository(IAoiDataRepository):
    def __init__(self, db: Session):
        self.db = db

    async def get_latest_assets(self, tenant_id: TenantId, aoi_id: UUID) -> dict:
        sql = text(
            """
            SELECT ndvi_s3_uri, anomaly_s3_uri, quicklook_s3_uri,
                   ndwi_s3_uri, ndmi_s3_uri, savi_s3_uri, false_color_s3_uri, true_color_s3_uri,
                   ndre_s3_uri, reci_s3_uri, gndvi_s3_uri, evi_s3_uri,
                   msi_s3_uri, nbr_s3_uri, bsi_s3_uri, ari_s3_uri, cri_s3_uri,
                   ndvi_mean, ndvi_min, ndvi_max, ndvi_std,
                   ndwi_mean, ndwi_min, ndwi_max, ndwi_std,
                   ndmi_mean, ndmi_min, ndmi_max, ndmi_std,
                   savi_mean, savi_min, savi_max, savi_std,
                   anomaly_mean, anomaly_std,
                   ndre_mean, ndre_std, reci_mean, reci_std,
                   gndvi_mean, gndvi_std, evi_mean, evi_std,
                   msi_mean, msi_std, nbr_mean, nbr_std,
                   bsi_mean, bsi_std, ari_mean, ari_std,
                   cri_mean, cri_std,
                   year, week
            FROM derived_assets
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
            ORDER BY year DESC, week DESC
            LIMIT 1
            """
        )
        result = self.db.execute(
            sql,
            {"tenant_id": str(tenant_id.value), "aoi_id": str(aoi_id)},
        ).fetchone()
        if not result:
            return {}
        return dict(result._mapping)

    async def get_history(self, tenant_id: TenantId, aoi_id: UUID, limit: int = 52) -> List[dict]:
        sql = text(
            """
            SELECT 
                year, week,
                ndvi_mean, ndvi_min, ndvi_max, ndvi_std,
                ndwi_mean, ndwi_min, ndwi_max, ndwi_std,
                ndmi_mean, ndmi_min, ndmi_max, ndmi_std,
                savi_mean, savi_min, savi_max, savi_std,
                anomaly_mean,
                ndre_mean, reci_mean, gndvi_mean, evi_mean,
                msi_mean, nbr_mean, bsi_mean, ari_mean, cri_mean
            FROM derived_assets
            WHERE tenant_id = :tenant_id AND aoi_id = :aoi_id
            ORDER BY year DESC, week DESC
            LIMIT :limit
            """
        )
        result = self.db.execute(
            sql,
            {"tenant_id": str(tenant_id.value), "aoi_id": str(aoi_id), "limit": limit},
        )
        return [dict(row._mapping) for row in result]
