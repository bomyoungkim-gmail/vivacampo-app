import base64
import json
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import OpportunitySignalView
from app.auth.dependencies import get_current_membership, CurrentMembership
from app.infrastructure.repositories import SignalRepository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/signals", response_model=List[OpportunitySignalView])
def list_signals(
    status: Optional[str] = None,
    signal_type: Optional[str] = None,
    aoi_id: Optional[UUID] = None,
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
    conditions = ["tenant_id = :tenant_id"]
    params = {
        "tenant_id": str(membership.tenant_id),
        "limit": min(limit, 100)
    }
    
    # Decode cursor
    if cursor:
        try:
            decoded = base64.b64decode(cursor).decode()
            cursor_id, cursor_created = decoded.split(":")
            conditions.append("(created_at, id) < (:cursor_created, :cursor_id)")
            params["cursor_created"] = cursor_created
            params["cursor_id"] = cursor_id
        except Exception as e:
            logger.warning("invalid_cursor", cursor=cursor, exc_info=e)
            raise HTTPException(status_code=400, detail="Invalid cursor")
    
    if status:
        conditions.append("status = :status")
        params["status"] = status
    
    if signal_type:
        conditions.append("signal_type = :signal_type")
        params["signal_type"] = signal_type
    
    if aoi_id:
        conditions.append("aoi_id = :aoi_id")
        params["aoi_id"] = str(aoi_id)
    
    sql = text(f"""
        SELECT id, aoi_id, year, week, signal_type, status, severity, 
               confidence, score, model_version, change_method, 
               evidence_json, recommended_actions, created_at
        FROM opportunity_signals
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC, id DESC
        LIMIT :limit + 1
    """)
    
    
    result = db.execute(sql, params)
    
    signals = []
    has_more = False
    
    for idx, row in enumerate(result):
        if idx >= limit:
            has_more = True
            break
        
        signals.append(OpportunitySignalView(
            id=row.id,
            aoi_id=row.aoi_id,
            year=row.year,
            week=row.week,
            signal_type=row.signal_type,
            status=row.status,
            severity=row.severity,
            confidence=row.confidence,
            score=row.score,
            model_version=row.model_version,
            change_method=row.change_method,
            evidence_json=json.loads(row.evidence_json) if isinstance(row.evidence_json, str) else (row.evidence_json or {}),
            recommended_actions=json.loads(row.recommended_actions) if isinstance(row.recommended_actions, str) else (row.recommended_actions or []),
            created_at=row.created_at
        ))
    
    # Generate next cursor
    next_cursor = None
    if has_more and signals:
        last_signal = signals[-1]
        cursor_str = f"{last_signal.id}:{last_signal.created_at}"
        next_cursor = base64.b64encode(cursor_str.encode()).decode()
    
    # Add next_cursor to response headers
    if next_cursor:
        response.headers["X-Next-Cursor"] = next_cursor
    
    return signals


@router.get("/signals/{signal_id}", response_model=OpportunitySignalView)
def get_signal(
    signal_id: str,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    Get a specific signal by ID.
    """
    from uuid import UUID
    
    signal_repo = SignalRepository(db)
    signal = signal_repo.get_by_id(
        signal_id=UUID(signal_id),
        tenant_id=membership.tenant_id
    )
    
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found"
        )
    
    return OpportunitySignalView.from_orm(signal)


@router.post("/signals/{signal_id}/ack", status_code=status.HTTP_200_OK)
def acknowledge_signal(
    signal_id: str,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    Acknowledge a signal (change status to ACK).
    """
    from uuid import UUID
    
    signal_repo = SignalRepository(db)
    signal = signal_repo.get_by_id(
        signal_id=UUID(signal_id),
        tenant_id=membership.tenant_id
    )
    
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal not found"
        )
    
    signal.status = "ACK"
    db.commit()
    
    return {"message": "Signal acknowledged"}
