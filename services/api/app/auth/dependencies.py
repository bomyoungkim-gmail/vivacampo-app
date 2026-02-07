from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from uuid import UUID
from app.database import get_db
from app.auth.utils import decode_session_token
from app.infrastructure.models import Identity, Membership, SystemAdmin

security = HTTPBearer()


class CurrentMembership:
    """
    Represents the current authenticated membership (tenant context).
    """
    def __init__(
        self,
        identity_id: UUID,
        tenant_id: UUID,
        membership_id: UUID,
        role: str
    ):
        self.identity_id = identity_id
        self.tenant_id = tenant_id
        self.membership_id = membership_id
        self.role = role


def get_current_membership(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    request: Request = None,
) -> CurrentMembership:
    """
    Extract and validate current membership from session token.
    This is the primary dependency for tenant-scoped endpoints.
    """
    token = credentials.credentials
    
    try:
        payload = decode_session_token(token)
    except ValueError as e:
        print(f"DEBUG: Token decode failed: {str(e)}") # Force print to stdout
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    identity_id = UUID(payload["sub"])
    tenant_id = UUID(payload["tenant_id"])
    membership_id = UUID(payload["membership_id"])
    role = payload["role"]

    print(f"DEBUG: Token Payload - Sub: {identity_id}, MemID: {membership_id}, Tenant: {tenant_id}")

    # Set tenant context for RLS in this transaction
    db.execute(text("SELECT set_config('app.is_system_admin', 'false', true)"))
    db.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )
    if request is not None:
        request.state.tenant_id = str(tenant_id)
    
    # Verify membership still exists and is ACTIVE (and matches token claims)
    membership = db.query(Membership).filter(
        Membership.id == membership_id,
        Membership.status == "ACTIVE"
    ).first()
    
    if not membership:
        print(f"DEBUG: Membership not found for ID {membership_id}")
        print(f"DEBUG: Query: db.query(Membership).filter(Membership.id == '{membership_id}', Membership.status == 'ACTIVE')")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Membership not found or inactive"
        )

    if membership.tenant_id != tenant_id or membership.identity_id != identity_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Membership does not match token claims"
        )
    
    return CurrentMembership(
        identity_id=identity_id,
        tenant_id=tenant_id,
        membership_id=membership_id,
        role=role
    )


def require_role(required_role: str):
    """
    Dependency factory to require specific role.
    Usage: Depends(require_role("TENANT_ADMIN"))
    """
    def role_checker(
        membership: CurrentMembership = Depends(get_current_membership)
    ):
        normalized_role = membership.role
        if normalized_role == "OPERATOR":
            normalized_role = "EDITOR"
        role_hierarchy = {
            "TENANT_ADMIN": 3,
            "EDITOR": 2,
            "VIEWER": 1
        }
        
        user_level = role_hierarchy.get(normalized_role, 0)
        required_level = role_hierarchy.get(required_role, 999)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_role}"
            )
        
        return membership
    
    return role_checker


def get_current_tenant_id(
    membership: CurrentMembership = Depends(get_current_membership),
) -> UUID:
    """
    Extract tenant_id from the current membership.
    Intended for multi-tenant endpoints to standardize tenant resolution.
    """
    return membership.tenant_id


def get_current_system_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    request: Request = None,
) -> SystemAdmin:
    """
    Verify current user is a system admin.
    Used for /v1/admin/* endpoints.
    """
    token = credentials.credentials
    
    try:
        # Decode system admin token (different issuer/audience)
        from jose import jwt
        from app.config import settings
        
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            audience=settings.system_admin_audience,
            issuer=settings.system_admin_issuer
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid system admin token"
        )
    
    identity_id = UUID(payload["sub"])

    # Set system admin context for RLS in this transaction
    db.execute(text("SELECT set_config('app.is_system_admin', 'true', true)"))
    db.execute(text("SELECT set_config('app.tenant_id', '', true)"))
    if request is not None:
        request.state.is_system_admin = True
    
    # Verify system admin exists and is ACTIVE
    system_admin = db.query(SystemAdmin).join(Identity).filter(
        SystemAdmin.identity_id == identity_id,
        SystemAdmin.status == "ACTIVE",
        Identity.status == "ACTIVE"
    ).first()
    
    if not system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System admin access required"
        )
    
    return system_admin
