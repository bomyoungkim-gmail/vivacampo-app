from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.auth.dependencies import require_role, CurrentMembership, get_current_tenant_id
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from app.schemas import (
    FieldCalibrationCreateRequest,
    FieldCalibrationCreateResponse,
    CalibrationResponse,
    PredictionResponse,
    FieldFeedbackCreateRequest,
    FieldFeedbackCreateResponse,
    AnalyticsEventRequest,
    AnalyticsEventResponse,
    AdoptionMetricsResponse,
)
from app.application.dtos.aois import (
    FieldCalibrationCreateCommand,
    CalibrationCommand,
    PredictionCommand,
    FieldFeedbackCommand,
)
from app.application.dtos.tenant_admin import GetAdoptionMetricsCommand
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.di_container import ApiContainer, get_container
from app.metrics import field_calibration_total

router = APIRouter(responses=DEFAULT_ERROR_RESPONSES, dependencies=[Depends(get_current_tenant_id)])


@router.post("/field-data", response_model=FieldCalibrationCreateResponse)
async def create_field_calibration(
    payload: FieldCalibrationCreateRequest,
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    container: ApiContainer = Depends(get_container),
):
    use_case = container.create_field_calibration_use_case()
    try:
        result = await use_case.execute(
            FieldCalibrationCreateCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                aoi_id=payload.aoi_id,
                observed_date=payload.date,
                metric_type=payload.metric_type,
                value=payload.value,
                unit=payload.unit,
            )
        )
    except ValueError as exc:
        if str(exc) == "AOI_NOT_FOUND":
            raise HTTPException(status_code=404, detail="AOI not found")
        raise HTTPException(status_code=422, detail=str(exc))

    field_calibration_total.labels(metric_type=payload.metric_type).inc()
    audit = container.audit_logger()
    audit.log(
        tenant_id=str(membership.tenant_id),
        actor_membership_id=str(membership.membership_id),
        action="CREATE",
        resource_type="field_calibration",
        resource_id=str(result.id),
        metadata={"aoi_id": str(payload.aoi_id), "metric_type": payload.metric_type, "unit": payload.unit},
    )

    return FieldCalibrationCreateResponse(id=result.id)


@router.get("/analytics/calibration", response_model=CalibrationResponse)
async def get_calibration(
    aoi_id: UUID,
    metric_type: str,
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    container: ApiContainer = Depends(get_container),
):
    use_case = container.calibration_use_case()
    if metric_type not in {"biomass", "yield"}:
        raise HTTPException(status_code=422, detail="Invalid metric_type")
    try:
        result = await use_case.execute(
            CalibrationCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                aoi_id=aoi_id,
                metric_type=metric_type,
            )
        )
    except ValueError as exc:
        if str(exc) == "INSUFFICIENT_DATA":
            raise HTTPException(status_code=422, detail="Insufficient data")
        raise HTTPException(status_code=422, detail=str(exc))

    return CalibrationResponse(
        r2=result.r2,
        coefficients=result.coefficients,
        sample_size=result.sample_size,
    )


@router.get("/analytics/prediction", response_model=PredictionResponse)
async def get_prediction(
    aoi_id: UUID,
    metric_type: str,
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    container: ApiContainer = Depends(get_container),
):
    use_case = container.prediction_use_case()
    try:
        result = await use_case.execute(
            PredictionCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                aoi_id=aoi_id,
                metric_type=metric_type,
            )
        )
    except ValueError as exc:
        message = str(exc)
        if message == "INSUFFICIENT_DATA":
            raise HTTPException(status_code=422, detail="Insufficient data")
        if message == "INVALID_METRIC":
            raise HTTPException(status_code=422, detail="Invalid metric_type")
        raise HTTPException(status_code=422, detail=message)

    return PredictionResponse(
        p10=result.p10,
        p50=result.p50,
        p90=result.p90,
        unit=result.unit,
        confidence=result.confidence,
        source=result.source,
    )


@router.post("/field-feedback", response_model=FieldFeedbackCreateResponse)
async def create_field_feedback(
    payload: FieldFeedbackCreateRequest,
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    container: ApiContainer = Depends(get_container),
):
    use_case = container.create_field_feedback_use_case()
    try:
        result = await use_case.execute(
            FieldFeedbackCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                aoi_id=payload.aoi_id,
                feedback_type=payload.type,
                message=payload.message,
                created_by_membership_id=membership.membership_id,
            )
        )
    except ValueError as exc:
        if str(exc) == "AOI_NOT_FOUND":
            raise HTTPException(status_code=404, detail="AOI not found")
        raise HTTPException(status_code=422, detail=str(exc))

    audit = container.audit_logger()
    audit.log(
        tenant_id=str(membership.tenant_id),
        actor_membership_id=str(membership.membership_id),
        action="CREATE",
        resource_type="field_feedback",
        resource_id=str(result.id),
        metadata={"aoi_id": str(payload.aoi_id), "feedback_type": payload.type},
    )

    return FieldFeedbackCreateResponse(id=result.id)


@router.post("/analytics/events", response_model=AnalyticsEventResponse)
async def track_analytics_event(
    payload: AnalyticsEventRequest,
    membership: CurrentMembership = Depends(require_role("EDITOR")),
    container: ApiContainer = Depends(get_container),
):
    audit = container.audit_logger()
    audit.log(
        tenant_id=str(membership.tenant_id),
        actor_membership_id=str(membership.membership_id),
        action="TRACK_EVENT",
        resource_type="frontend_event",
        resource_id=None,
        metadata={
            "event": payload.event_name,
            "phase": payload.phase,
            "props": payload.metadata,
        },
    )

    return AnalyticsEventResponse()


@router.get("/analytics/adoption", response_model=AdoptionMetricsResponse)
async def get_adoption_metrics(
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    container: ApiContainer = Depends(get_container),
):
    use_case = container.adoption_metrics_use_case()
    result = await use_case.execute(
        GetAdoptionMetricsCommand(tenant_id=TenantId(value=membership.tenant_id))
    )
    return AdoptionMetricsResponse(
        events=result.get("events", []),
        phases=result.get("phases", []),
    )
