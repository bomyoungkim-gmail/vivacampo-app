import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import OpportunitySignalView
from app.auth.dependencies import get_current_membership, CurrentMembership, get_current_tenant_id
from app.domain.value_objects.tenant_id import TenantId
from app.application.dtos.signals import AckSignalCommand, GetSignalCommand, ListSignalsCommand
from app.infrastructure.di_container import ApiContainer

logger = logging.getLogger(__name__)

router = APIRouter(responses=DEFAULT_ERROR_RESPONSES, dependencies=[Depends(get_current_tenant_id)])


@router.get("/signals", response_model=List[OpportunitySignalView])
async def list_signals(
    status: Optional[str] = None,
    signal_type: Optional[str] = None,
    aoi_id: Optional[UUID] = None,
    farm_id: Optional[UUID] = None,
    cursor: Optional[str] = None,  # Base64 encoded: {id}:{created_at}
    limit: int = 20,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db),
    response: Response = Response() # Inject Response object to set headers
):
    """
    List opportunity signals for the current tenant.
    Uses cursor-based pagination for scalability.
    """
    container = ApiContainer()
    use_case = container.list_signals_use_case(db)

    try:
        result = await use_case.execute(
            ListSignalsCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                status=status,
                signal_type=signal_type,
                aoi_id=aoi_id,
                farm_id=farm_id,
                cursor=cursor,
                limit=limit,
            )
        )
    except Exception as e:
        logger.warning("invalid_cursor", cursor=cursor, exc_info=e)
        raise HTTPException(status_code=400, detail="Invalid cursor")

    if result.next_cursor:
        response.headers["X-Next-Cursor"] = result.next_cursor

    return [
        OpportunitySignalView(
            id=item.id,
            aoi_id=item.aoi_id,
            aoi_name=item.aoi_name,
            year=item.year,
            week=item.week,
            signal_type=item.signal_type,
            status=item.status,
            severity=item.severity,
            confidence=item.confidence,
            score=item.score,
            model_version=item.model_version,
            change_method=item.change_method,
            evidence_json=item.evidence_json or {},
            recommended_actions=item.recommended_actions or [],
            created_at=item.created_at,
        )
        for item in result.items
    ]


@router.get("/signals/{signal_id}", response_model=OpportunitySignalView)
async def get_signal(
    signal_id: str,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    Get a specific signal by ID.
    """
    container = ApiContainer()
    use_case = container.get_signal_use_case(db)
    signal = await use_case.execute(
        GetSignalCommand(tenant_id=TenantId(value=membership.tenant_id), signal_id=UUID(signal_id))
    )

    if not signal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found")

    return OpportunitySignalView(
        id=signal.id,
        aoi_id=signal.aoi_id,
        aoi_name=signal.aoi_name,
        year=signal.year,
        week=signal.week,
        signal_type=signal.signal_type,
        status=signal.status,
        severity=signal.severity,
        confidence=signal.confidence,
        score=signal.score,
        model_version=signal.model_version,
        change_method=signal.change_method,
        evidence_json=signal.evidence_json or {},
        recommended_actions=signal.recommended_actions or [],
        created_at=signal.created_at,
    )


@router.post("/signals/{signal_id}/ack", status_code=status.HTTP_200_OK)
async def acknowledge_signal(
    signal_id: UUID, # Changed type hint from str to UUID
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    Acknowledge a signal (change status to ACK).
    """
    container = ApiContainer()
    use_case = container.ack_signal_use_case(db)
    ok = await use_case.execute(
        AckSignalCommand(tenant_id=TenantId(value=membership.tenant_id), signal_id=signal_id)
    )

    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signal not found")

    return {"message": "Signal acknowledged"}