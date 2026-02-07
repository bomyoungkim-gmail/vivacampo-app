import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.dtos.auth import SignupCommand, LoginCommand
from app.application.use_cases.auth import SignupUseCase, LoginUseCase
from app.auth.utils import hash_password
from app.domain.ports.auth_repository import IAuthRepository


class _StubAuthRepo(IAuthRepository):
    def __init__(self):
        self.identities = {}
        self.memberships = []
        self.tenants = []
        self.workspaces = []

    async def get_identity_by_email(self, email: str):
        return next((i for i in self.identities.values() if i['email'] == email), None)

    async def get_identity_by_email_provider(self, email: str, provider: str):
        return next(
            (i for i in self.identities.values() if i['email'] == email and i.get('provider') == provider),
            None,
        )

    async def get_identity_by_reset_token(self, token: str):
        return None

    async def create_identity_local(self, email: str, name: str, password_hash: str) -> dict:
        identity_id = uuid4()
        identity = {
            'id': identity_id,
            'email': email,
            'name': name,
            'status': 'ACTIVE',
            'password_hash': password_hash,
            'provider': 'local',
            'created_at': datetime.now(timezone.utc),
        }
        self.identities[str(identity_id)] = identity
        return identity

    async def update_identity_password(self, identity_id, password_hash: str) -> None:
        if str(identity_id) in self.identities:
            self.identities[str(identity_id)]['password_hash'] = password_hash

    async def set_password_reset(self, identity_id, token: str, expires_at) -> None:
        return None

    async def clear_password_reset(self, identity_id) -> None:
        return None

    async def create_tenant(self, tenant_type: str, name: str, plan: str, quotas: dict) -> dict:
        tenant_id = uuid4()
        tenant = {
            'id': tenant_id,
            'type': tenant_type,
            'name': name,
            'plan': plan,
        }
        self.tenants.append(tenant)
        return tenant

    async def create_membership(self, tenant_id, identity_id, role: str, status: str) -> dict:
        membership_id = uuid4()
        membership = {
            'id': membership_id,
            'tenant_id': tenant_id,
            'identity_id': identity_id,
            'role': role,
            'status': status,
        }
        self.memberships.append(membership)
        return membership

    async def list_workspaces(self, identity_id) -> list[dict]:
        return self.workspaces


@pytest.mark.asyncio
async def test_signup_use_case_creates_identity_and_workspace():
    repo = _StubAuthRepo()
    use_case = SignupUseCase(repo)

    command = SignupCommand(
        email='user@example.com',
        password='supersecret',
        full_name='User Example',
        company_name='Viva Campo',
    )

    # Prepare workspace to be returned
    tenant_id = uuid4()
    membership_id = uuid4()
    repo.workspaces.append({
        'tenant_id': tenant_id,
        'tenant_type': 'COMPANY',
        'tenant_name': 'Viva Campo',
        'membership_id': membership_id,
        'role': 'TENANT_ADMIN',
        'status': 'ACTIVE',
    })

    result = await use_case.execute(command)

    assert result.identity.email == 'user@example.com'
    assert result.identity.status == 'ACTIVE'
    assert result.workspaces
    assert result.access_token


@pytest.mark.asyncio
async def test_login_use_case_validates_password():
    repo = _StubAuthRepo()
    use_case = LoginUseCase(repo)

    password_hash = hash_password('correct-password')
    identity_id = uuid4()
    repo.identities[str(identity_id)] = {
        'id': identity_id,
        'email': 'login@example.com',
        'name': 'Login User',
        'status': 'ACTIVE',
        'password_hash': password_hash,
        'provider': 'local',
    }
    repo.workspaces.append({
        'tenant_id': uuid4(),
        'tenant_type': 'PERSONAL',
        'tenant_name': 'Login Workspace',
        'membership_id': uuid4(),
        'role': 'TENANT_ADMIN',
        'status': 'ACTIVE',
    })

    result = await use_case.execute(LoginCommand(email='login@example.com', password='correct-password'))
    assert result.access_token

    with pytest.raises(ValueError):
        await use_case.execute(LoginCommand(email='login@example.com', password='wrong'))
