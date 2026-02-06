import asyncio
from datetime import datetime
from uuid import uuid4

from app.application.dtos.farms import CreateFarmCommand, ListFarmsCommand
from app.application.use_cases.farms import CreateFarmUseCase, ListFarmsUseCase
from app.domain.entities.farm import Farm
from app.domain.ports.farm_repository import IFarmRepository
from app.domain.value_objects.tenant_id import TenantId


class _StubFarmRepo(IFarmRepository):
    def __init__(self):
        self.created = []

    async def find_by_id_and_tenant(self, farm_id, tenant_id):
        return None

    async def find_all_by_tenant(self, tenant_id):
        return self.created

    async def create(self, farm: Farm) -> Farm:
        self.created.append(farm)
        return farm


def test_create_farm_use_case_returns_result():
    repo = _StubFarmRepo()
    use_case = CreateFarmUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(
            CreateFarmCommand(tenant_id=tenant_id, name="Farm 1", timezone="America/Sao_Paulo")
        )

    result = asyncio.run(run())
    assert result.name == "Farm 1"
    assert result.tenant_id == tenant_id.value


def test_list_farms_use_case_returns_results():
    repo = _StubFarmRepo()
    use_case = ListFarmsUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    repo.created.append(
        Farm(
            tenant_id=tenant_id,
            name="Farm 2",
            timezone="America/Sao_Paulo",
            created_at=datetime.utcnow(),
        )
    )

    async def run():
        return await use_case.execute(ListFarmsCommand(tenant_id=tenant_id))

    results = asyncio.run(run())
    assert len(results) == 1
    assert results[0].name == "Farm 2"
