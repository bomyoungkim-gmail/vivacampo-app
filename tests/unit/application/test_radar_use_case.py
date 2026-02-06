import asyncio
from uuid import uuid4

from app.application.dtos.radar import RadarHistoryCommand
from app.application.use_cases.radar import GetRadarHistoryUseCase
from app.domain.value_objects.tenant_id import TenantId


class _StubRadarRepo:
    def __init__(self, rows):
        self.rows = rows

    async def get_history(self, tenant_id, aoi_id, year=None, limit=52):
        return self.rows


def test_get_radar_history_use_case():
    tenant_id = TenantId(value=uuid4())
    aoi_id = uuid4()
    rows = [{"year": 2024, "week": 1, "rvi_mean": 0.5}]
    repo = _StubRadarRepo(rows)
    use_case = GetRadarHistoryUseCase(repo)

    async def run():
        return await use_case.execute(
            RadarHistoryCommand(tenant_id=tenant_id, aoi_id=aoi_id, limit=10)
        )

    result = asyncio.run(run())
    assert result == rows
