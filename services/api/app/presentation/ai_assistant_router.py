from fastapi import APIRouter, Depends, HTTPException, status
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership, require_role, get_current_tenant_id
from app.ai_assistant.workflow import AIAssistantWorkflow
from app.application.dtos.ai_assistant import (
    CreateThreadCommand,
    GetApprovalThreadCommand,
    GetMessagesCommand,
    ListApprovalsCommand,
    ListThreadsCommand,
)
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.di_container import ApiContainer
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()
router = APIRouter(responses=DEFAULT_ERROR_RESPONSES, dependencies=[Depends(get_current_tenant_id)])


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

    container = ApiContainer()
    use_case = container.create_ai_thread_use_case(db)
    row = await use_case.execute(
        CreateThreadCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            aoi_id=thread_data.aoi_id,
            signal_id=thread_data.signal_id,
            membership_id=membership.membership_id,
            provider=provider,
            model=model,
        )
    )
    
    return ThreadView(
        id=row["id"],
        aoi_id=thread_data.aoi_id,
        signal_id=thread_data.signal_id,
        provider=provider,
        model=model,
        status="OPEN",
        created_at=str(row["created_at"])
    )


@router.get("/ai-assistant/threads", response_model=List[ThreadView])
async def list_threads(
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    List all AI assistant threads for the current tenant.
    """
    container = ApiContainer()
    use_case = container.list_ai_threads_use_case(db)
    rows = await use_case.execute(
        ListThreadsCommand(tenant_id=TenantId(value=membership.tenant_id))
    )
    return [
        ThreadView(
            id=row["id"],
            aoi_id=row["aoi_id"],
            signal_id=row["signal_id"],
            provider=row["provider"],
            model=row["model"],
            status=row["status"],
            created_at=str(row["created_at"]),
        )
        for row in rows
    ]


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
    container = ApiContainer()
    use_case = container.ai_messages_use_case(db)
    messages = await use_case.execute(
        GetMessagesCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            thread_id=thread_id,
        )
    )
    return [MessageView(role=m["role"], content=m["content"]) for m in messages]


@router.get("/ai-assistant/approvals", response_model=List[ApprovalView])
async def list_approvals(
    pending_only: bool = True,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    List approval requests for the current tenant.
    """
    container = ApiContainer()
    use_case = container.list_ai_approvals_use_case(db)
    rows = await use_case.execute(
        ListApprovalsCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            pending_only=pending_only,
        )
    )
    import json
    approvals = []
    for row in rows:
        approvals.append(
            ApprovalView(
                id=row["id"],
                tool_name=row["tool_name"],
                tool_payload=json.loads(row["tool_payload"]),
                decision=row["decision"],
                created_at=str(row["created_at"]),
            )
        )
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
    container = ApiContainer()
    use_case = container.ai_approval_thread_use_case(db)
    thread_id = await use_case.execute(
        GetApprovalThreadCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            approval_id=approval_id,
        )
    )

    if not thread_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval not found"
        )
    
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