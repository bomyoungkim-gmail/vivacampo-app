from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership, require_role
from app.ai_assistant.workflow import AIAssistantWorkflow
from pydantic import BaseModel, Field
from sqlalchemy import text
import structlog

logger = structlog.get_logger()
router = APIRouter()


# Schemas
class ThreadCreate(BaseModel):
    aoi_id: Optional[UUID] = None
    signal_id: Optional[UUID] = None
    provider: Optional[str] = Field(None, description="openai, anthropic, or gemini")
    model: Optional[str] = None


class ThreadView(BaseModel):
    id: UUID
    aoi_id: Optional[UUID]
    signal_id: Optional[UUID]
    provider: str
    model: str
    status: str
    created_at: str


class MessageCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    language: str = Field("pt-BR", description="pt-BR or en")


class MessageView(BaseModel):
    role: str
    content: str


class ApprovalDecision(BaseModel):
    decision: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    note: Optional[str] = Field(None, max_length=500)


class ApprovalView(BaseModel):
    id: UUID
    tool_name: str
    tool_payload: dict
    decision: str
    created_at: str


# Endpoints
@router.post("/ai-assistant/threads", response_model=ThreadView, status_code=status.HTTP_201_CREATED)
async def create_thread(
    thread_data: ThreadCreate,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    Create a new AI assistant thread.
    """
    from app.config import settings
    
    provider = thread_data.provider or settings.ai_assistant_provider
    model = thread_data.model or settings.ai_assistant_model
    
    sql = text("""
        INSERT INTO ai_assistant_threads
        (tenant_id, aoi_id, signal_id, created_by_membership_id, provider, model, status)
        VALUES (:tenant_id, :aoi_id, :signal_id, :membership_id, :provider, :model, 'OPEN')
        RETURNING id, created_at
    """)
    
    result = db.execute(sql, {
        "tenant_id": str(membership.tenant_id),
        "aoi_id": str(thread_data.aoi_id) if thread_data.aoi_id else None,
        "signal_id": str(thread_data.signal_id) if thread_data.signal_id else None,
        "membership_id": str(membership.membership_id),
        "provider": provider,
        "model": model
    })
    db.commit()
    
    row = result.fetchone()
    
    return ThreadView(
        id=row.id,
        aoi_id=thread_data.aoi_id,
        signal_id=thread_data.signal_id,
        provider=provider,
        model=model,
        status="OPEN",
        created_at=str(row.created_at)
    )


@router.get("/ai-assistant/threads", response_model=List[ThreadView])
async def list_threads(
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    List all AI assistant threads for the current tenant.
    """
    sql = text("""
        SELECT id, aoi_id, signal_id, provider, model, status, created_at
        FROM ai_assistant_threads
        WHERE tenant_id = :tenant_id
        ORDER BY created_at DESC
        LIMIT 50
    """)
    
    result = db.execute(sql, {"tenant_id": str(membership.tenant_id)})
    
    threads = []
    for row in result:
        threads.append(ThreadView(
            id=row.id,
            aoi_id=row.aoi_id,
            signal_id=row.signal_id,
            provider=row.provider,
            model=row.model,
            status=row.status,
            created_at=str(row.created_at)
        ))
    
    return threads


@router.post("/ai-assistant/threads/{thread_id}/messages")
async def send_message(
    thread_id: UUID,
    message_data: MessageCreate,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    Send a message to an AI assistant thread.
    """
    try:
        workflow = AIAssistantWorkflow(
            thread_id=str(thread_id),
            tenant_id=str(membership.tenant_id),
            db=db
        )
        
        response = workflow.process_message(
            message_data.text,
            language=message_data.language
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("message_processing_failed", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.get("/ai-assistant/threads/{thread_id}/messages", response_model=List[MessageView])
async def get_messages(
    thread_id: UUID,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    Get conversation history for a thread.
    """
    sql = text("""
        SELECT state_json
        FROM ai_assistant_checkpoints
        WHERE thread_id = :thread_id AND tenant_id = :tenant_id
        ORDER BY step DESC
        LIMIT 1
    """)
    
    result = db.execute(sql, {
        "thread_id": str(thread_id),
        "tenant_id": str(membership.tenant_id)
    }).fetchone()
    
    if not result:
        return []
    
    import json
    state = json.loads(result.state_json)
    messages = state.get('messages', [])
    
    return [MessageView(role=m['role'], content=m['content']) for m in messages if m['role'] != 'system']


@router.get("/ai-assistant/approvals", response_model=List[ApprovalView])
async def list_approvals(
    pending_only: bool = True,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    List approval requests for the current tenant.
    """
    sql = text("""
        SELECT id, tool_name, tool_payload, decision, created_at
        FROM ai_assistant_approvals
        WHERE tenant_id = :tenant_id
        AND (:pending_only = false OR decision = 'PENDING')
        ORDER BY created_at DESC
        LIMIT 50
    """)
    
    result = db.execute(sql, {
        "tenant_id": str(membership.tenant_id),
        "pending_only": pending_only
    })
    
    import json
    approvals = []
    for row in result:
        approvals.append(ApprovalView(
            id=row.id,
            tool_name=row.tool_name,
            tool_payload=json.loads(row.tool_payload),
            decision=row.decision,
            created_at=str(row.created_at)
        ))
    
    return approvals


@router.post("/ai-assistant/approvals/{approval_id}/decide")
async def decide_approval(
    approval_id: UUID,
    decision_data: ApprovalDecision,
    membership: CurrentMembership = Depends(require_role("OPERATOR")),
    db: Session = Depends(get_db)
):
    """
    Approve or reject an AI assistant action.
    Requires OPERATOR or TENANT_ADMIN role.
    """
    # Get thread_id from approval
    sql = text("""
        SELECT thread_id
        FROM ai_assistant_approvals
        WHERE id = :approval_id AND tenant_id = :tenant_id
    """)
    
    result = db.execute(sql, {
        "approval_id": str(approval_id),
        "tenant_id": str(membership.tenant_id)
    }).fetchone()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval not found"
        )
    
    thread_id = result.thread_id
    
    try:
        workflow = AIAssistantWorkflow(
            thread_id=str(thread_id),
            tenant_id=str(membership.tenant_id),
            db=db
        )
        
        response = workflow.process_approval(
            approval_id=str(approval_id),
            decision=decision_data.decision,
            decided_by_membership_id=str(membership.membership_id),
            note=decision_data.note
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error("approval_processing_failed", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process approval"
        )
