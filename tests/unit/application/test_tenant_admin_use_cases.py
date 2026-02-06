import asyncio
from uuid import uuid4

from app.application.dtos.tenant_admin import InviteMemberCommand, UpdateMemberRoleCommand
from app.application.use_cases.tenant_admin import InviteMemberUseCase, UpdateMemberRoleUseCase
from app.domain.value_objects.tenant_id import TenantId


class _StubTenantRepo:
    def __init__(self):
        self.identity = None
        self.memberships = {}
        self.admin_count = 2

    async def get_identity_by_email(self, email):
        return self.identity

    async def membership_exists(self, tenant_id, identity_id):
        return False

    async def create_identity(self, email, name):
        return uuid4()

    async def create_membership(self, tenant_id, identity_id, role):
        return {"id": uuid4(), "created_at": "now"}

    async def get_membership_role(self, tenant_id, membership_id):
        return "TENANT_ADMIN"

    async def count_active_admins(self, tenant_id):
        return self.admin_count

    async def update_membership_role(self, tenant_id, membership_id, role):
        return True


def test_invite_member_use_case():
    repo = _StubTenantRepo()
    use_case = InviteMemberUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(
            InviteMemberCommand(
                tenant_id=tenant_id,
                email="test@example.com",
                name="Test",
                role="OPERATOR",
            )
        )

    result = asyncio.run(run())
    assert result["status"] == "INVITED"


def test_update_member_role_use_case():
    repo = _StubTenantRepo()
    use_case = UpdateMemberRoleUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(
            UpdateMemberRoleCommand(
                tenant_id=tenant_id,
                membership_id=uuid4(),
                role="OPERATOR",
            )
        )

    result = asyncio.run(run())
    assert result["new_role"] == "OPERATOR"
