"""Auth use cases (signup/login/forgot/reset)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Optional
from uuid import UUID

from app.application.dtos.auth import (
    AuthResult,
    ForgotPasswordCommand,
    IdentityResult,
    LoginCommand,
    MessageResult,
    ResetPasswordCommand,
    SignupCommand,
    WorkspaceResult,
)
from app.auth.utils import (
    create_password_reset_token,
    create_session_token,
    decode_password_reset_token,
    hash_password,
    verify_password,
)
from app.domain.ports.auth_repository import IAuthRepository


class SignupUseCase:
    def __init__(self, auth_repo: IAuthRepository):
        self.auth_repo = auth_repo

    async def execute(self, command: SignupCommand) -> AuthResult:
        existing = await self.auth_repo.get_identity_by_email(command.email)
        if existing:
            raise ValueError("EMAIL_ALREADY_EXISTS")

        password_hash = hash_password(command.password)
        identity = await self.auth_repo.create_identity_local(
            email=command.email,
            name=command.full_name,
            password_hash=password_hash,
        )

        tenant_type = "COMPANY" if command.company_name else "PERSONAL"
        tenant_name = command.company_name or f"{command.full_name}'s Workspace"
        tenant = await self.auth_repo.create_tenant(
            tenant_type=tenant_type,
            name=tenant_name,
            plan="BASIC",
            quotas={},
        )

        membership = await self.auth_repo.create_membership(
            tenant_id=tenant["id"],
            identity_id=identity["id"],
            role="TENANT_ADMIN",
            status="ACTIVE",
        )

        workspaces = await self._build_workspaces(identity_id=identity["id"])
        access_token = create_session_token(
            tenant_id=membership["tenant_id"],
            membership_id=membership["id"],
            identity_id=identity["id"],
            role=membership["role"],
        )

        return AuthResult(
            identity=IdentityResult(
                id=identity["id"],
                email=identity["email"],
                name=identity["name"],
                status=identity["status"],
            ),
            workspaces=workspaces,
            access_token=access_token,
        )

    async def _build_workspaces(self, identity_id: UUID) -> list[WorkspaceResult]:
        rows = await self.auth_repo.list_workspaces(identity_id)
        return [
            WorkspaceResult(
                tenant_id=row["tenant_id"],
                tenant_type=row["tenant_type"],
                tenant_name=row["tenant_name"],
                membership_id=row["membership_id"],
                role=row["role"],
                status=row["status"],
            )
            for row in rows
        ]


class LoginUseCase:
    def __init__(self, auth_repo: IAuthRepository):
        self.auth_repo = auth_repo

    async def execute(self, command: LoginCommand) -> AuthResult:
        identity = await self.auth_repo.get_identity_by_email_provider(command.email, "local")
        if not identity:
            raise ValueError("INVALID_CREDENTIALS")
        if identity.get("status") != "ACTIVE":
            raise ValueError("IDENTITY_INACTIVE")
        if not identity.get("password_hash"):
            raise ValueError("INVALID_CREDENTIALS")
        if not verify_password(command.password, identity["password_hash"]):
            raise ValueError("INVALID_CREDENTIALS")

        workspaces = await self._build_workspaces(identity_id=identity["id"])
        default = _pick_default_workspace(workspaces)
        access_token: Optional[str] = None
        if default:
            access_token = create_session_token(
                tenant_id=default.tenant_id,
                membership_id=default.membership_id,
                identity_id=identity["id"],
                role=default.role,
            )

        return AuthResult(
            identity=IdentityResult(
                id=identity["id"],
                email=identity["email"],
                name=identity["name"],
                status=identity["status"],
            ),
            workspaces=workspaces,
            access_token=access_token,
        )

    async def _build_workspaces(self, identity_id: UUID) -> list[WorkspaceResult]:
        rows = await self.auth_repo.list_workspaces(identity_id)
        return [
            WorkspaceResult(
                tenant_id=row["tenant_id"],
                tenant_type=row["tenant_type"],
                tenant_name=row["tenant_name"],
                membership_id=row["membership_id"],
                role=row["role"],
                status=row["status"],
            )
            for row in rows
        ]


class ForgotPasswordUseCase:
    def __init__(self, auth_repo: IAuthRepository):
        self.auth_repo = auth_repo

    async def execute(self, command: ForgotPasswordCommand) -> MessageResult:
        identity = await self.auth_repo.get_identity_by_email_provider(command.email, "local")
        if not identity:
            return MessageResult(message="If the email exists, a reset link has been sent.")

        token = create_password_reset_token(identity_id=identity["id"], email=identity["email"])
        expires_at = datetime.now(UTC) + timedelta(minutes=15)
        await self.auth_repo.set_password_reset(identity_id=identity["id"], token=token, expires_at=expires_at)

        # TODO: send email with reset link
        return MessageResult(message="If the email exists, a reset link has been sent.")


class ResetPasswordUseCase:
    def __init__(self, auth_repo: IAuthRepository):
        self.auth_repo = auth_repo

    async def execute(self, command: ResetPasswordCommand) -> MessageResult:
        try:
            payload = decode_password_reset_token(command.token)
        except ValueError:
            raise ValueError("RESET_TOKEN_INVALID")
        identity = await self.auth_repo.get_identity_by_reset_token(command.token)
        if not identity:
            raise ValueError("RESET_TOKEN_INVALID")

        expires_at = identity.get("password_reset_expires_at")
        if not expires_at or expires_at < datetime.now(UTC):
            raise ValueError("RESET_TOKEN_EXPIRED")

        if str(identity["id"]) != payload.get("sub"):
            raise ValueError("RESET_TOKEN_INVALID")

        new_hash = hash_password(command.new_password)
        await self.auth_repo.update_identity_password(identity_id=identity["id"], password_hash=new_hash)
        await self.auth_repo.clear_password_reset(identity_id=identity["id"])

        return MessageResult(message="Password updated.")


def _pick_default_workspace(workspaces: list[WorkspaceResult]) -> Optional[WorkspaceResult]:
    active = [w for w in workspaces if w.status == "ACTIVE"]
    if not active:
        return None
    for workspace in active:
        if workspace.tenant_type == "PERSONAL":
            return workspace
    return active[0]
