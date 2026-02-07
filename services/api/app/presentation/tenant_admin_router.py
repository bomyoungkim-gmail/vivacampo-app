from fastapi import APIRouter, Depends, HTTPException, status
from app.presentation.error_responses import DEFAULT_ERROR_RESPONSES
from typing import List
from uuid import UUID

from app.auth.dependencies import get_current_membership, CurrentMembership, require_role, get_current_tenant_id
from app.schemas import (
    InviteMemberRequest, MembershipView, MembershipRolePatch,
    MembershipStatusPatch, TenantSettingsView, TenantSettingsPatch,
    AuditLogView
)
from app.domain.quotas import QuotaExceededError
from app.application.dtos.tenant_admin import (
    GetTenantAuditLogCommand,
    GetTenantSettingsCommand,
    InviteMemberCommand,
    ListMembersCommand,
    UpdateMemberRoleCommand,
    UpdateMemberStatusCommand,
    UpdateTenantSettingsCommand,
)
from app.domain.value_objects.tenant_id import TenantId
from app.infrastructure.di_container import ApiContainer, get_container
import structlog

logger = structlog.get_logger()
router = APIRouter(responses=DEFAULT_ERROR_RESPONSES, dependencies=[Depends(get_current_tenant_id)])


@router.get("/admin/tenant/members", response_model=List[MembershipView])
async def list_members(
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    container: ApiContainer = Depends(get_container)
):
    """
    List all members of the current tenant.
    Requires TENANT_ADMIN role.
    """
    use_case = container.list_tenant_members_use_case()
    rows = await use_case.execute(
        ListMembersCommand(tenant_id=TenantId(value=membership.tenant_id))
    )
    return [
        MembershipView(
            id=row["id"],
            identity_id=row["identity_id"],
            email=row["email"],
            name=row["name"],
            role=row["role"],
            status=row["status"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


@router.post("/admin/tenant/members/invite", status_code=status.HTTP_201_CREATED)
async def invite_member(
    invite_data: InviteMemberRequest,
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    container: ApiContainer = Depends(get_container)
):
    """
    Invite a new member to the tenant.
    Requires TENANT_ADMIN role.
    Enforces member quota.
    """
    quota_service = container.quota_service()

    # Check quota
    try:
        quota_service.check_member_quota(str(membership.tenant_id))
    except QuotaExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Member quota exceeded: {e.current}/{e.limit}"
        )
    
    use_case = container.invite_tenant_member_use_case()
    try:
        row = await use_case.execute(
            InviteMemberCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                email=invite_data.email,
                name=invite_data.name,
                role=invite_data.role,
            )
        )
    except ValueError as exc:
        if str(exc) == "MEMBERSHIP_EXISTS":
            raise HTTPException(
                status_code=400,
                detail="User is already a member of this tenant"
            )
        if str(exc) == "INVALID_ROLE":
            raise HTTPException(
                status_code=400,
                detail="Invalid role. Choose EDITOR or VIEWER."
            )
        raise
    
    # Audit log
    audit = container.audit_logger()
    audit.log_membership_invite(
        tenant_id=str(membership.tenant_id),
        actor_id=str(membership.membership_id),
        invited_email=invite_data.email,
        role=invite_data.role
    )
    
    # TODO: Send invitation email
    
    return {
        "membership_id": row["membership_id"],
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
    container: ApiContainer = Depends(get_container)
):
    """
    Update member role.
    Requires TENANT_ADMIN role.
    Cannot demote the last TENANT_ADMIN.
    """
    use_case = container.update_member_role_use_case()
    try:
        result = await use_case.execute(
            UpdateMemberRoleCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                membership_id=membership_id,
                role=role_patch.role,
            )
        )
    except ValueError as exc:
        if str(exc) == "LAST_ADMIN":
            raise HTTPException(
                status_code=400,
                detail="Cannot demote the last TENANT_ADMIN"
            )
        raise

    if not result:
        raise HTTPException(status_code=404, detail="Membership not found")

    old_role = result["old_role"]
    
    # Audit log
    audit = container.audit_logger()
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
    container: ApiContainer = Depends(get_container)
):
    """
    Update member status (ACTIVE/SUSPENDED).
    Requires TENANT_ADMIN role.
    Cannot suspend the last TENANT_ADMIN.
    """
    use_case = container.update_member_status_use_case()
    try:
        result = await use_case.execute(
            UpdateMemberStatusCommand(
                tenant_id=TenantId(value=membership.tenant_id),
                membership_id=membership_id,
                status=status_patch.status,
            )
        )
    except ValueError as exc:
        if str(exc) == "LAST_ADMIN":
            raise HTTPException(
                status_code=400,
                detail="Cannot suspend the last active TENANT_ADMIN"
            )
        raise

    if not result:
        raise HTTPException(status_code=404, detail="Membership not found")

    old_status = result["old_status"]
    
    # Audit log
    audit = container.audit_logger()
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
    container: ApiContainer = Depends(get_container)
):
    """Get tenant settings"""
    use_case = container.get_tenant_settings_use_case()
    result = await use_case.execute(
        GetTenantSettingsCommand(tenant_id=TenantId(value=membership.tenant_id))
    )

    if not result:
        return TenantSettingsView(
            tier="PERSONAL",
            min_valid_pixel_ratio=0.15,
            alert_thresholds={},
        )

    import json
    return TenantSettingsView(
        tier=result["tier"],
        min_valid_pixel_ratio=result["min_valid_pixel_ratio"],
        alert_thresholds=json.loads(result["alert_thresholds_json"]) if result["alert_thresholds_json"] else {},
    )


@router.patch("/admin/tenant/settings")
async def update_tenant_settings(
    settings_patch: TenantSettingsPatch,
    membership: CurrentMembership = Depends(require_role("TENANT_ADMIN")),
    container: ApiContainer = Depends(get_container)
):
    """
    Update tenant settings.
    Requires TENANT_ADMIN role.
    """
    get_use_case = container.get_tenant_settings_use_case()
    current = await get_use_case.execute(
        GetTenantSettingsCommand(tenant_id=TenantId(value=membership.tenant_id))
    )

    changes = {}
    if settings_patch.min_valid_pixel_ratio is not None and current:
        changes["min_valid_pixel_ratio"] = {
            "before": current.get("min_valid_pixel_ratio"),
            "after": settings_patch.min_valid_pixel_ratio,
        }

    update_use_case = container.update_tenant_settings_use_case()
    await update_use_case.execute(
        UpdateTenantSettingsCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            min_valid_pixel_ratio=settings_patch.min_valid_pixel_ratio,
            alert_thresholds=settings_patch.alert_thresholds,
        )
    )
    
    # Audit log
    if changes:
        audit = container.audit_logger()
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
    container: ApiContainer = Depends(get_container)
):
    """
    Get audit log for the tenant.
    Requires TENANT_ADMIN role.
    """
    use_case = container.tenant_audit_log_use_case()
    rows = await use_case.execute(
        GetTenantAuditLogCommand(
            tenant_id=TenantId(value=membership.tenant_id),
            limit=limit,
        )
    )

    logs = []
    import json
    for row in rows:
        logs.append(
            AuditLogView(
                id=row["id"],
                action=row["action"],
                resource_type=row["resource_type"],
                resource_id=str(row["resource_id"]) if row["resource_id"] else None,
                changes=json.loads(row["changes_json"]) if row["changes_json"] else None,
                metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else None,
                created_at=row["created_at"],
            )
        )
    return logs
