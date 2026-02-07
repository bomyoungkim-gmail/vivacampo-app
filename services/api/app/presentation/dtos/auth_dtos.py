from __future__ import annotations

from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.application.dtos.auth import AuthResult, MessageResult


class SignupRequestDTO(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=120)
    company_name: Optional[str] = Field(default=None, min_length=2, max_length=120)

    model_config = ConfigDict(frozen=True)


class LoginRequestDTO(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(frozen=True)


class ForgotPasswordRequestDTO(BaseModel):
    email: EmailStr

    model_config = ConfigDict(frozen=True)


class ResetPasswordRequestDTO(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

    model_config = ConfigDict(frozen=True)


class IdentityDTO(BaseModel):
    id: UUID
    email: str
    name: str
    status: str


class WorkspaceDTO(BaseModel):
    tenant_id: UUID
    tenant_type: str
    tenant_name: str
    membership_id: UUID
    role: str
    status: str


class AuthResponseDTO(BaseModel):
    identity: IdentityDTO
    workspaces: List[WorkspaceDTO]
    access_token: Optional[str] = None

    @classmethod
    def from_result(cls, result: AuthResult) -> "AuthResponseDTO":
        return cls(
            identity=IdentityDTO(
                id=result.identity.id,
                email=result.identity.email,
                name=result.identity.name,
                status=result.identity.status,
            ),
            workspaces=[
                WorkspaceDTO(
                    tenant_id=ws.tenant_id,
                    tenant_type=ws.tenant_type,
                    tenant_name=ws.tenant_name,
                    membership_id=ws.membership_id,
                    role=ws.role,
                    status=ws.status,
                )
                for ws in result.workspaces
            ],
            access_token=result.access_token,
        )


class MessageResponseDTO(BaseModel):
    message: str

    @classmethod
    def from_result(cls, result: MessageResult) -> "MessageResponseDTO":
        return cls(message=result.message)
