"""AOI use cases using domain ports and DTOs."""
from __future__ import annotations

from typing import List

from app.application.decorators import require_tenant
from app.application.dtos.aois import (
    CreateAoiCommand,
    ListAoisCommand,
    AoiResult,
    SimulateSplitCommand,
    SimulateSplitResult,
    SplitPolygonResult,
    SplitAoiCommand,
    SplitAoiResult,
    AoiStatusCommand,
    AoiStatusResult,
    AoiStatusItem,
    FieldCalibrationCreateCommand,
    FieldCalibrationResult,
    CalibrationCommand,
    CalibrationResult,
    PredictionCommand,
    PredictionResult,
    FieldFeedbackCommand,
    FieldFeedbackResult,
)
from app.domain.entities.aoi import AOI
from app.domain.ports.aoi_repository import IAOIRepository
from app.domain.ports.job_repository import IJobRepository
from app.domain.ports.field_calibration_repository import IFieldCalibrationRepository
from app.domain.ports.aoi_data_repository import IAoiDataRepository
from app.domain.ports.yield_forecast_repository import IYieldForecastRepository
from app.domain.ports.field_feedback_repository import IFieldFeedbackRepository
from app.domain.utils.unit_conversion import to_kg_ha
from app.domain.ports.split_batch_repository import ISplitBatchRepository
from app.domain.ports.aoi_spatial_repository import IAoiSpatialRepository
from app.domain.value_objects.area_hectares import AreaHectares
from app.domain.value_objects.geometry_wkt import GeometryWkt


class CreateAoiUseCase:
    def __init__(self, aoi_repo: IAOIRepository):
        self.aoi_repo = aoi_repo

    @require_tenant
    async def execute(self, command: CreateAoiCommand) -> AoiResult:
        aoi = AOI(
            tenant_id=command.tenant_id,
            parent_aoi_id=command.parent_aoi_id,
            farm_id=command.farm_id,
            name=command.name,
            use_type=command.use_type,
            geometry_wkt=GeometryWkt(value=command.geometry_wkt),
            area_hectares=AreaHectares(value=1.0),
        )
        created = await self.aoi_repo.create(aoi)
        return AoiResult(
            id=created.id,
            tenant_id=created.tenant_id.value,
            parent_aoi_id=created.parent_aoi_id,
            farm_id=created.farm_id,
            name=created.name,
            use_type=created.use_type,
            status=created.status,
            area_ha=created.area_hectares.value,
            geometry=created.geometry_wkt.value,
            created_at=created.created_at,
        )


class ListAoisUseCase:
    def __init__(self, aoi_repo: IAOIRepository):
        self.aoi_repo = aoi_repo

    @require_tenant
    async def execute(self, command: ListAoisCommand) -> List[AoiResult]:
        aois = await self.aoi_repo.list_by_tenant(
            tenant_id=command.tenant_id,
            farm_id=command.farm_id,
            status=command.status,
            limit=command.limit,
        )
        return [
            AoiResult(
                id=aoi.id,
                tenant_id=aoi.tenant_id.value,
                parent_aoi_id=aoi.parent_aoi_id,
                farm_id=aoi.farm_id,
                name=aoi.name,
                use_type=aoi.use_type,
                status=aoi.status,
                area_ha=aoi.area_hectares.value,
                geometry=aoi.geometry_wkt.value,
                created_at=aoi.created_at,
            )
            for aoi in aois
        ]


class SimulateSplitUseCase:
    def __init__(self, spatial_repo: IAoiSpatialRepository):
        self.spatial_repo = spatial_repo

    @require_tenant
    async def execute(self, command: SimulateSplitCommand) -> SimulateSplitResult:
        polygons = await self.spatial_repo.simulate_split(
            tenant_id=command.tenant_id,
            geometry_wkt=command.geometry_wkt,
            mode=command.mode,
            target_count=command.target_count,
        )
        warnings = []
        for idx, poly in enumerate(polygons, start=1):
            if poly["area_ha"] > command.max_area_ha:
                warnings.append(f"talhao_{idx}_exceeds_max_area")
        return SimulateSplitResult(
            polygons=[
                SplitPolygonResult(
                    geometry_wkt=poly["geometry_wkt"],
                    area_ha=poly["area_ha"],
                )
                for poly in polygons
            ],
            warnings=warnings,
        )


class SplitAoiUseCase:
    def __init__(self, aoi_repo: IAOIRepository, split_batch_repo: ISplitBatchRepository):
        self.aoi_repo = aoi_repo
        self.split_batch_repo = split_batch_repo

    @require_tenant
    async def execute(self, command: SplitAoiCommand) -> SplitAoiResult:
        if command.idempotency_key:
            existing = await self.split_batch_repo.get_by_key(command.tenant_id, command.idempotency_key)
            if existing:
                return SplitAoiResult(created_ids=existing, idempotent=True)

        parent = await self.aoi_repo.get_by_id(command.tenant_id, command.parent_aoi_id)
        if not parent:
            raise ValueError("PARENT_AOI_NOT_FOUND")

        if not command.polygons:
            raise ValueError("POLYGONS_REQUIRED")

        created_ids = []
        for idx, polygon in enumerate(command.polygons, start=1):
            _, area_ha = await self.aoi_repo.normalize_geometry(polygon.geometry_wkt)
            if area_ha > command.max_area_ha:
                raise ValueError(f"TALHAO_{idx}_EXCEEDS_MAX_AREA")

        for idx, polygon in enumerate(command.polygons, start=1):
            name = polygon.name or f"Talhao {idx}"
            aoi = AOI(
                tenant_id=command.tenant_id,
                parent_aoi_id=command.parent_aoi_id,
                farm_id=parent.farm_id,
                name=name,
                use_type=parent.use_type,
                geometry_wkt=GeometryWkt(value=polygon.geometry_wkt),
                area_hectares=AreaHectares(value=1.0),
            )
            created = await self.aoi_repo.create(aoi)
            created_ids.append(created.id)

        if command.idempotency_key:
            await self.split_batch_repo.create(
                tenant_id=command.tenant_id,
                parent_aoi_id=command.parent_aoi_id,
                idempotency_key=command.idempotency_key,
                created_ids=created_ids,
            )

        return SplitAoiResult(created_ids=created_ids, idempotent=False)


class AoiStatusUseCase:
    def __init__(self, job_repo: IJobRepository):
        self.job_repo = job_repo

    @require_tenant
    async def execute(self, command: AoiStatusCommand) -> AoiStatusResult:
        if not command.aoi_ids:
            return AoiStatusResult(items=[])

        rows = await self.job_repo.latest_status_by_aois(command.tenant_id, command.aoi_ids)
        by_aoi = {row["aoi_id"]: row for row in rows}
        items = []
        for aoi_id in command.aoi_ids:
            row = by_aoi.get(aoi_id)
            job_status = row["status"] if row else None
            is_processing = job_status in {"PENDING", "RUNNING"}
            items.append(
                AoiStatusItem(
                    aoi_id=aoi_id,
                    is_processing=is_processing,
                    job_status=job_status,
                    job_type=row["job_type"] if row else None,
                    updated_at=row["updated_at"] if row else None,
                )
            )
        return AoiStatusResult(items=items)


class CreateFieldCalibrationUseCase:
    def __init__(
        self,
        aoi_repo: IAOIRepository,
        calibration_repo: IFieldCalibrationRepository,
    ):
        self.aoi_repo = aoi_repo
        self.calibration_repo = calibration_repo

    @require_tenant
    async def execute(self, command: FieldCalibrationCreateCommand) -> FieldCalibrationResult:
        aoi = await self.aoi_repo.get_by_id(command.tenant_id, command.aoi_id)
        if not aoi:
            raise ValueError("AOI_NOT_FOUND")

        value_kg_ha = to_kg_ha(command.value, command.unit)
        calibration_id = await self.calibration_repo.create(
            tenant_id=command.tenant_id,
            aoi_id=command.aoi_id,
            observed_date=_parse_date(command.observed_date),
            metric_type=command.metric_type,
            value=value_kg_ha,
            unit="kg_ha",
            source=command.source,
        )
        return FieldCalibrationResult(
            id=calibration_id,
            aoi_id=command.aoi_id,
            observed_date=command.observed_date,
            metric_type=command.metric_type,
            value=value_kg_ha,
            unit="kg_ha",
            source=command.source,
        )


class GetCalibrationUseCase:
    def __init__(
        self,
        calibration_repo: IFieldCalibrationRepository,
        aoi_data_repo: IAoiDataRepository,
    ):
        self.calibration_repo = calibration_repo
        self.aoi_data_repo = aoi_data_repo

    @require_tenant
    async def execute(self, command: CalibrationCommand) -> CalibrationResult:
        rows = await self.calibration_repo.list_by_aoi_metric(
            tenant_id=command.tenant_id,
            aoi_id=command.aoi_id,
            metric_type=command.metric_type,
        )
        points = []
        for row in rows:
            observed = row["observed_date"]
            year, week, _ = observed.isocalendar()
            index_row = await self.aoi_data_repo.get_index_for_week(
                tenant_id=command.tenant_id,
                aoi_id=command.aoi_id,
                year=year,
                week=week,
            )
            if not index_row or index_row.get("ndvi_mean") is None:
                continue
            points.append((float(index_row["ndvi_mean"]), float(row["value"])))

        if len(points) < 2:
            raise ValueError("INSUFFICIENT_DATA")

        slope, intercept, r2 = _linear_regression(points)
        return CalibrationResult(
            r2=r2,
            coefficients={"intercept": intercept, "slope": slope},
            sample_size=len(points),
        )


class GetPredictionUseCase:
    def __init__(self, yield_repo: IYieldForecastRepository):
        self.yield_repo = yield_repo

    @require_tenant
    async def execute(self, command: PredictionCommand) -> PredictionResult:
        if command.metric_type != "yield":
            raise ValueError("INVALID_METRIC")

        latest = await self.yield_repo.get_latest_by_aoi(command.tenant_id, command.aoi_id)
        if latest:
            return PredictionResult(
                p10=float(latest["index_p10"]),
                p50=float(latest["index_p50"]),
                p90=float(latest["index_p90"]),
                unit="kg_ha",
                confidence=float(latest.get("confidence", 0.6) or 0.6),
                source="aoi_forecast",
            )

        summary = await self.yield_repo.get_tenant_summary(command.tenant_id)
        if summary:
            return PredictionResult(
                p10=float(summary["p10"]),
                p50=float(summary["p50"]),
                p90=float(summary["p90"]),
                unit="kg_ha",
                confidence=0.5,
                source="tenant_average",
            )

        raise ValueError("INSUFFICIENT_DATA")


class CreateFieldFeedbackUseCase:
    def __init__(self, aoi_repo: IAOIRepository, feedback_repo: IFieldFeedbackRepository):
        self.aoi_repo = aoi_repo
        self.feedback_repo = feedback_repo

    @require_tenant
    async def execute(self, command: FieldFeedbackCommand) -> FieldFeedbackResult:
        aoi = await self.aoi_repo.get_by_id(command.tenant_id, command.aoi_id)
        if not aoi:
            raise ValueError("AOI_NOT_FOUND")

        feedback_id = await self.feedback_repo.create(
            tenant_id=command.tenant_id,
            aoi_id=command.aoi_id,
            feedback_type=command.feedback_type,
            message=command.message,
            created_by_membership_id=command.created_by_membership_id,
        )
        return FieldFeedbackResult(id=feedback_id)


def _linear_regression(points: list[tuple[float, float]]) -> tuple[float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0:
        slope = 0.0
    else:
        slope = sum((x - x_mean) * (y - y_mean) for x, y in points) / denom
    intercept = y_mean - slope * x_mean
    sse = sum((y - (slope * x + intercept)) ** 2 for x, y in points)
    sst = sum((y - y_mean) ** 2 for y in ys)
    r2 = 0.0 if sst == 0 else max(0.0, 1 - (sse / sst))
    return slope, intercept, r2


def _parse_date(value: str):
    from datetime import datetime

    return datetime.strptime(value, "%Y-%m-%d").date()
