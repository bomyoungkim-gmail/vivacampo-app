from __future__ import annotations

from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SignupCommand(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=120)
    company_name: Optional[str] = Field(default=None, min_length=2, max_length=120)

    model_config = ConfigDict(frozen=True)


class LoginCommand(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(frozen=True)


class ForgotPasswordCommand(BaseModel):
    email: EmailStr

    model_config = ConfigDict(frozen=True)


class ResetPasswordCommand(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

    model_config = ConfigDict(frozen=True)


class IdentityResult(BaseModel):
    id: UUID
    email: str
    name: str
    status: str


class WorkspaceResult(BaseModel):
    tenant_id: UUID
    tenant_type: str
    tenant_name: str
    membership_id: UUID
    role: str
    status: str


class AuthResult(BaseModel):
    identity: IdentityResult
    workspaces: List[WorkspaceResult]
    access_token: Optional[str]


class MessageResult(BaseModel):
    message: str
