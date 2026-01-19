from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.auth.dependencies import get_current_membership, CurrentMembership, require_role
from app.schemas import (
    InviteMemberRequest, MembershipView, MembershipRolePatch, 
    MembershipStatusPatch, TenantSettingsView, TenantSettingsPatch,
    AuditLogView
)
from app.domain.quotas import check_member_quota, QuotaExceededError
from app.domain.audit import get_audit_logger
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.get("/admin/tenant/members", response_model=List[MembershipView])
async def list_members(
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    db: Session = Depends(get_db)
):
    """
    List all members of the current tenant.
    Requires TENANT_ADMIN role.
    """
    sql = text("""
        SELECT m.id, m.identity_id, i.email, i.name, m.role, m.status, m.created_at
        FROM memberships m
        JOIN identities i ON m.identity_id = i.id
        WHERE m.tenant_id = :tenant_id
        ORDER BY m.created_at DESC
    """)
    
    result = db.execute(sql, {"tenant_id": str(membership.tenant_id)})
    
    members = []
    for row in result:
        members.append(MembershipView(
            id=row.id,
            identity_id=row.identity_id,
            email=row.email,
            name=row.name,
            role=row.role,
            status=row.status,
            created_at=row.created_at
        ))
    
    return members


@router.post("/admin/tenant/members/invite", status_code=status.HTTP_201_CREATED)
async def invite_member(
    invite_data: InviteMemberRequest,
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    db: Session = Depends(get_db)
):
    """
    Invite a new member to the tenant.
    Requires TENANT_ADMIN role.
    Enforces member quota.
    """
    # Check quota
    try:
        check_member_quota(str(membership.tenant_id), db)
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Member quota exceeded: {e.current}/{e.limit}"
        )
    
    # Check if identity exists
    sql = text("SELECT id FROM identities WHERE email = :email")
    result = db.execute(sql, {"email": invite_data.email}).fetchone()
    
    if result:
        identity_id = result.id
        
        # Check if already member
        sql = text("""
            SELECT id FROM memberships 
            WHERE tenant_id = :tenant_id AND identity_id = :identity_id
        """)
        existing = db.execute(sql, {
            "tenant_id": str(membership.tenant_id),
            "identity_id": str(identity_id)
        }).fetchone()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="User is already a member of this tenant"
            )
    else:
        # Create placeholder identity (will be claimed on first login)
        sql = text("""
            INSERT INTO identities (provider, subject, email, name, status)
            VALUES ('local', :email, :email, :name, 'PENDING')
            RETURNING id
        """)
        result = db.execute(sql, {
            "email": invite_data.email,
            "name": invite_data.name
        })
        identity_id = result.fetchone()[0]
    
    # Create membership with INVITED status
    sql = text("""
        INSERT INTO memberships (tenant_id, identity_id, role, status)
        VALUES (:tenant_id, :identity_id, :role, 'INVITED')
        RETURNING id, created_at
    """)
    
    result = db.execute(sql, {
        "tenant_id": str(membership.tenant_id),
        "identity_id": str(identity_id),
        "role": invite_data.role
    })
    db.commit()
    
    row = result.fetchone()
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log_membership_invite(
        tenant_id=str(membership.tenant_id),
        actor_id=str(membership.membership_id),
        invited_email=invite_data.email,
        role=invite_data.role
    )
    
    # TODO: Send invitation email
    
    return {
        "membership_id": row.id,
        "email": invite_data.email,
        "role": invite_data.role,
        "status": "INVITED",
        "message": "Invitation sent successfully"
    }


@router.patch("/admin/tenant/members/{membership_id}/role")
async def update_member_role(
    membership_id: UUID,
    role_patch: MembershipRolePatch,
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    db: Session = Depends(get_db)
):
    """
    Update member role.
    Requires TENANT_ADMIN role.
    Cannot demote the last TENANT_ADMIN.
    """
    # Get current membership
    sql = text("""
        SELECT role FROM memberships
        WHERE id = :membership_id AND tenant_id = :tenant_id
    """)
    
    result = db.execute(sql, {
        "membership_id": str(membership_id),
        "tenant_id": str(membership.tenant_id)
    }).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Membership not found")
    
    old_role = result.role
    
    # Check if demoting last TENANT_ADMIN
    if old_role == "TENANT_ADMIN" and role_patch.role != "TENANT_ADMIN":
        sql = text("""
            SELECT COUNT(*) as count FROM memberships
            WHERE tenant_id = :tenant_id AND role = 'TENANT_ADMIN' AND status = 'ACTIVE'
        """)
        result = db.execute(sql, {"tenant_id": str(membership.tenant_id)}).fetchone()
        
        if result.count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot demote the last TENANT_ADMIN"
            )
    
    # Update role
    sql = text("""
        UPDATE memberships
        SET role = :role
        WHERE id = :membership_id AND tenant_id = :tenant_id
    """)
    
    db.execute(sql, {
        "role": role_patch.role,
        "membership_id": str(membership_id),
        "tenant_id": str(membership.tenant_id)
    })
    db.commit()
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log_membership_role_change(
        tenant_id=str(membership.tenant_id),
        actor_id=str(membership.membership_id),
        membership_id=str(membership_id),
        old_role=old_role,
        new_role=role_patch.role
    )
    
    return {"message": "Role updated successfully", "new_role": role_patch.role}


@router.patch("/admin/tenant/members/{membership_id}/status")
async def update_member_status(
    membership_id: UUID,
    status_patch: MembershipStatusPatch,
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    db: Session = Depends(get_db)
):
    """
    Update member status (ACTIVE/SUSPENDED).
    Requires TENANT_ADMIN role.
    Cannot suspend the last TENANT_ADMIN.
    """
    # Get current membership
    sql = text("""
        SELECT role, status FROM memberships
        WHERE id = :membership_id AND tenant_id = :tenant_id
    """)
    
    result = db.execute(sql, {
        "membership_id": str(membership_id),
        "tenant_id": str(membership.tenant_id)
    }).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Membership not found")
    
    old_status = result.status
    
    # Check if suspending last active TENANT_ADMIN
    if result.role == "TENANT_ADMIN" and status_patch.status == "SUSPENDED":
        sql = text("""
            SELECT COUNT(*) as count FROM memberships
            WHERE tenant_id = :tenant_id AND role = 'TENANT_ADMIN' AND status = 'ACTIVE'
        """)
        count_result = db.execute(sql, {"tenant_id": str(membership.tenant_id)}).fetchone()
        
        if count_result.count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot suspend the last active TENANT_ADMIN"
            )
    
    # Update status
    sql = text("""
        UPDATE memberships
        SET status = :status
        WHERE id = :membership_id AND tenant_id = :tenant_id
    """)
    
    db.execute(sql, {
        "status": status_patch.status,
        "membership_id": str(membership_id),
        "tenant_id": str(membership.tenant_id)
    })
    db.commit()
    
    # Audit log
    audit = get_audit_logger(db)
    audit.log_membership_status_change(
        tenant_id=str(membership.tenant_id),
        actor_id=str(membership.membership_id),
        membership_id=str(membership_id),
        old_status=old_status,
        new_status=status_patch.status
    )
    
    return {"message": "Status updated successfully", "new_status": status_patch.status}


@router.get("/admin/tenant/settings", response_model=TenantSettingsView)
async def get_tenant_settings(
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    db: Session = Depends(get_db)
):
    """Get tenant settings"""
    sql = text("""
        SELECT tier, min_valid_pixel_ratio, alert_thresholds_json
        FROM tenant_settings
        WHERE tenant_id = :tenant_id
    """)
    
    result = db.execute(sql, {"tenant_id": str(membership.tenant_id)}).fetchone()
    
    if not result:
        # Return defaults
        return TenantSettingsView(
            tier="PERSONAL",
            min_valid_pixel_ratio=0.15,
            alert_thresholds={}
        )
    
    import json
    return TenantSettingsView(
        tier=result.tier,
        min_valid_pixel_ratio=result.min_valid_pixel_ratio,
        alert_thresholds=json.loads(result.alert_thresholds_json) if result.alert_thresholds_json else {}
    )


@router.patch("/admin/tenant/settings")
async def update_tenant_settings(
    settings_patch: TenantSettingsPatch,
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    db: Session = Depends(get_db)
):
    """
    Update tenant settings.
    Requires TENANT_ADMIN role.
    """
    # Get current settings
    sql = text("SELECT min_valid_pixel_ratio FROM tenant_settings WHERE tenant_id = :tenant_id")
    current = db.execute(sql, {"tenant_id": str(membership.tenant_id)}).fetchone()
    
    changes = {}
    
    if settings_patch.min_valid_pixel_ratio is not None:
        if current:
            changes["min_valid_pixel_ratio"] = {
                "before": current.min_valid_pixel_ratio,
                "after": settings_patch.min_valid_pixel_ratio
            }
    
    # Upsert settings
    import json
    sql = text("""
        INSERT INTO tenant_settings (tenant_id, min_valid_pixel_ratio, alert_thresholds_json)
        VALUES (:tenant_id, :min_valid, :thresholds)
        ON CONFLICT (tenant_id) DO UPDATE
        SET min_valid_pixel_ratio = COALESCE(:min_valid, tenant_settings.min_valid_pixel_ratio),
            alert_thresholds_json = COALESCE(:thresholds, tenant_settings.alert_thresholds_json)
    """)
    
    db.execute(sql, {
        "tenant_id": str(membership.tenant_id),
        "min_valid": settings_patch.min_valid_pixel_ratio,
        "thresholds": json.dumps(settings_patch.alert_thresholds) if settings_patch.alert_thresholds else None
    })
    db.commit()
    
    # Audit log
    if changes:
        audit = get_audit_logger(db)
        audit.log_tenant_settings_change(
            tenant_id=str(membership.tenant_id),
            actor_id=str(membership.membership_id),
            changes=changes
        )
    
    return {"message": "Settings updated successfully"}


@router.get("/admin/tenant/audit", response_model=List[AuditLogView])
async def get_audit_log(
    limit: int = 50,
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    db: Session = Depends(get_db)
):
    """
    Get audit log for the tenant.
    Requires TENANT_ADMIN role.
    """
    sql = text("""
        SELECT id, action, resource_type, resource_id, changes_json, metadata_json, created_at
        FROM audit_log
        WHERE tenant_id = :tenant_id
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    
    result = db.execute(sql, {
        "tenant_id": str(membership.tenant_id),
        "limit": min(limit, 100)
    })
    
    logs = []
    import json
    for row in result:
        logs.append(AuditLogView(
            id=row.id,
            action=row.action,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            changes=json.loads(row.changes_json) if row.changes_json else None,
            metadata=json.loads(row.metadata_json) if row.metadata_json else None,
            created_at=row.created_at
        ))
    
    return logs
