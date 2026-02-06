import asyncio
from datetime import datetime
from uuid import uuid4

from app.application.dtos.signals import AckSignalCommand, GetSignalCommand, ListSignalsCommand
from app.application.use_cases.signals import AckSignalUseCase, GetSignalUseCase, ListSignalsUseCase
from app.domain.ports.signal_repository import ISignalRepository
from app.domain.value_objects.tenant_id import TenantId


class _StubSignalRepo(ISignalRepository):
    def __init__(self):
        self.signals = []
        self.acked = set()

    async def list_signals(
        self,
        tenant_id,
        status=None,
        signal_type=None,
        aoi_id=None,
        farm_id=None,
        cursor_id=None,
        cursor_created=None,
        limit=20,
    ):
        return self.signals, False

    async def get_signal(self, tenant_id, signal_id):
        for signal in self.signals:
            if signal["id"] == signal_id:
                return signal
        return None

    async def acknowledge(self, tenant_id, signal_id):
        self.acked.add(signal_id)
        return True


def _signal(signal_id):
    return {
        "id": signal_id,
        "aoi_id": uuid4(),
        "aoi_name": "AOI 1",
        "year": 2025,
        "week": 1,
        "signal_type": "VIGOR_DROP",
        "status": "OPEN",
        "severity": "LOW",
        "confidence": "LOW",
        "score": 0.5,
        "model_version": "v1",
        "change_method": "BFast",
        "evidence_json": {},
        "recommended_actions": ["Check"],
        "created_at": datetime.utcnow(),
    }


def test_list_signals_use_case():
    repo = _StubSignalRepo()
    signal_id = uuid4()
    repo.signals.append(_signal(signal_id))
    use_case = ListSignalsUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(ListSignalsCommand(tenant_id=tenant_id))

    result = asyncio.run(run())
    assert len(result.items) == 1
    assert result.items[0].id == signal_id


def test_get_signal_use_case():
    repo = _StubSignalRepo()
    signal_id = uuid4()
    repo.signals.append(_signal(signal_id))
    use_case = GetSignalUseCase(repo)
    tenant_id = TenantId(value=uuid4())

    async def run():
        return await use_case.execute(GetSignalCommand(tenant_id=tenant_id, signal_id=signal_id))

    result = asyncio.run(run())
    assert result is not None
    assert result.id == signal_id


def test_ack_signal_use_case():
    repo = _StubSignalRepo()
    use_case = AckSignalUseCase(repo)
    tenant_id = TenantId(value=uuid4())
    signal_id = uuid4()

    async def run():
        return await use_case.execute(AckSignalCommand(tenant_id=tenant_id, signal_id=signal_id))

    ok = asyncio.run(run())
    assert ok is True
    assert signal_id in repo.acked
