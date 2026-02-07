"""Tenant admin use cases."""
from __future__ import annotations

import json

from app.application.decorators import require_tenant
from app.application.dtos.tenant_admin import (
    GetTenantAuditLogCommand,
    GetTenantSettingsCommand,
    InviteMemberCommand,
    ListMembersCommand,
    UpdateMemberRoleCommand,
    UpdateMemberStatusCommand,
    UpdateTenantSettingsCommand,
)
from app.domain.ports.tenant_admin_repository import ITenantAdminRepository


class ListMembersUseCase:
    def __init__(self, repo: ITenantAdminRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: ListMembersCommand) -> list[dict]:
        return await self.repo.list_members(command.tenant_id)


class InviteMemberUseCase:
    def __init__(self, repo: ITenantAdminRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: InviteMemberCommand) -> dict:
        if command.role not in {"EDITOR", "VIEWER"}:
            raise ValueError("INVALID_ROLE")
        identity = await self.repo.get_identity_by_email(command.email)
        if identity:
            identity_id = identity["id"]
            if await self.repo.membership_exists(command.tenant_id, identity_id):
                raise ValueError("MEMBERSHIP_EXISTS")
        else:
            identity_id = await self.repo.create_identity(command.email, command.name or command.email)

        membership = await self.repo.create_membership(command.tenant_id, identity_id, command.role)
        return {
            "membership_id": membership["id"],
            "email": command.email,
            "role": command.role,
            "status": "INVITED",
            "created_at": membership["created_at"],
        }


class UpdateMemberRoleUseCase:
    def __init__(self, repo: ITenantAdminRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: UpdateMemberRoleCommand) -> dict | None:
        old_role = await self.repo.get_membership_role(command.tenant_id, command.membership_id)
        if old_role is None:
            return None

        if old_role == "TENANT_ADMIN" and command.role != "TENANT_ADMIN":
            count = await self.repo.count_active_admins(command.tenant_id)
            if count <= 1:
                raise ValueError("LAST_ADMIN")

        await self.repo.update_membership_role(command.tenant_id, command.membership_id, command.role)
        return {"old_role": old_role, "new_role": command.role}


class UpdateMemberStatusUseCase:
    def __init__(self, repo: ITenantAdminRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: UpdateMemberStatusCommand) -> dict | None:
        current = await self.repo.get_membership_role_status(command.tenant_id, command.membership_id)
        if not current:
            return None

        if current["role"] == "TENANT_ADMIN" and command.status == "SUSPENDED":
            count = await self.repo.count_active_admins(command.tenant_id)
            if count <= 1:
                raise ValueError("LAST_ADMIN")

        await self.repo.update_membership_status(command.tenant_id, command.membership_id, command.status)
        return {"old_status": current["status"], "new_status": command.status, "role": current["role"]}


class GetTenantSettingsUseCase:
    def __init__(self, repo: ITenantAdminRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: GetTenantSettingsCommand) -> dict | None:
        return await self.repo.get_tenant_settings(command.tenant_id)


class UpdateTenantSettingsUseCase:
    def __init__(self, repo: ITenantAdminRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: UpdateTenantSettingsCommand) -> dict:
        await self.repo.upsert_tenant_settings(
            tenant_id=command.tenant_id,
            min_valid_pixel_ratio=command.min_valid_pixel_ratio,
            alert_thresholds_json=json.dumps(command.alert_thresholds) if command.alert_thresholds else None,
        )
        return {
            "min_valid_pixel_ratio": command.min_valid_pixel_ratio,
            "alert_thresholds": command.alert_thresholds,
        }


class GetTenantAuditLogUseCase:
    def __init__(self, repo: ITenantAdminRepository):
        self.repo = repo

    @require_tenant
    async def execute(self, command: GetTenantAuditLogCommand) -> list[dict]:
        return await self.repo.list_audit_logs(command.tenant_id, command.limit)
