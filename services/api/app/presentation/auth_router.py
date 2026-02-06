from fastapi import APIRouter, Depends, HTTPException, status
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    OIDCLoginRequest,
    IdentityView,
    WorkspaceListResponse,
    WorkspaceView,
    WorkspaceSwitchRequest,
    SessionTokenResponse
)
from app.infrastructure.models import Identity, Tenant, Membership
from app.auth.dependencies import get_current_membership, CurrentMembership
from app.auth.utils import validate_oidc_token, create_session_token
from app.config import settings
import uuid

router = APIRouter(responses=DEFAULT_ERROR_RESPONSES)

@router.post("/auth/oidc/login", response_model=dict)
async def oidc_login(
    request: OIDCLoginRequest,
    db: Session = Depends(get_db)
):
    """
    OIDC login endpoint.
    - Validates OIDC token
    - Creates identity if doesn't exist
    - If INDIVIDUAL (no memberships), creates PERSONAL tenant + TENANT_ADMIN membership
    - Returns identity + workspaces + access_token
    """
    # Validate OIDC token
    try:
        token_data = validate_oidc_token(request.id_token, request.provider)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
    # Find or create identity
    identity = db.query(Identity).filter(
        Identity.provider == request.provider,
        Identity.subject == token_data["subject"]
    ).first()
    
    if not identity:
        identity = Identity(
            provider=request.provider,
            subject=token_data["subject"],
            email=token_data["email"],
            name=token_data["name"],
            status="ACTIVE"
        )
        db.add(identity)
        db.commit()
        db.refresh(identity)
    
    # Check if user has any memberships
    memberships = db.query(Membership).filter(
        Membership.identity_id == identity.id
    ).all()
    
    # If no memberships (INDIVIDUAL), create ENTERPRISE tenant (for Dev/MVP)
    if not memberships:
        # Create COMPANY tenant
        personal_tenant = Tenant(
            type="COMPANY",
            name=f"{identity.name}'s Workspace",
            status="ACTIVE",
            plan="ENTERPRISE",
            quotas={}
        )
        db.add(personal_tenant)
        db.commit()
        db.refresh(personal_tenant)
        
        # Create TENANT_ADMIN membership
        membership = Membership(
            tenant_id=personal_tenant.id,
            identity_id=identity.id,
            role="TENANT_ADMIN",
            status="ACTIVE"
        )
        db.add(membership)
        db.commit()
        db.refresh(membership)
        
        memberships = [membership]
    
    # Build workspaces list
    workspaces = []
    for m in memberships:
        tenant = db.query(Tenant).filter(Tenant.id == m.tenant_id).first()
        if tenant and m.status == "ACTIVE":
            workspaces.append(WorkspaceView(
                tenant_id=tenant.id,
                tenant_type=tenant.type,
                tenant_name=tenant.name,
                membership_id=m.id,
                role=m.role,
                status=m.status
            ))
            
    # Select default workspace for session (Prefer PERSONAL, then first active)
    active_workspaces = [w for w in workspaces if w.status == "ACTIVE"]
    default_workspace = next(
        (w for w in active_workspaces if w.tenant_type == "PERSONAL"),
        active_workspaces[0] if active_workspaces else None
    )
    
    access_token = None
    if default_workspace:
        access_token = create_session_token(
            tenant_id=default_workspace.tenant_id,
            membership_id=default_workspace.membership_id,
            identity_id=identity.id,
            role=default_workspace.role
        )
    
    return {
        "identity": IdentityView.from_orm(identity),
        "workspaces": workspaces,
        "access_token": access_token
    }


@router.post("/auth/workspaces/switch", response_model=SessionTokenResponse)
async def switch_workspace(
    request: WorkspaceSwitchRequest,
    membership: CurrentMembership = Depends(get_current_membership),
    db: Session = Depends(get_db)
):
    """
    Switch workspace (tenant).
    Returns session token with active_tenant_id + membership_id + role.
    
    """
    # Find membership for the same identity
    membership = db.query(Membership).filter(
        Membership.tenant_id == request.tenant_id,
        Membership.identity_id == membership.identity_id,
        Membership.status == "ACTIVE"
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membership not found or inactive"
        )
    
    # Create session token
    token = create_session_token(
        tenant_id=membership.tenant_id,
        membership_id=membership.id,
        identity_id=membership.identity_id,
        role=membership.role
    )
    
    return SessionTokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_seconds=settings.session_token_ttl_minutes * 60
    )


@router.get("/me")
async def get_current_user():
    """
    Get current user info.
    TODO: Implement with proper auth.
    """
    return {"message": "Not implemented yet"}
